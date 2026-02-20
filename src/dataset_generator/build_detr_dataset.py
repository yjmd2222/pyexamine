import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple

# Reuse file discovery and robust JSON loading utilities
from .build_dataset import _iter_code_files, _read_file, _load_json, _get_value


DEFAULT_SEPARATOR = "[file]"


def _safe_relpath(path: str, base: str) -> str:
    try:
        common = os.path.commonpath([os.path.abspath(base), os.path.abspath(path)])
    except ValueError:
        common = ""
    if common == os.path.abspath(base):
        return os.path.relpath(path, base)
    return path


def _line_start_offsets(text: str) -> List[int]:
    # 0-based char offsets for the start of each 1-indexed line.
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _build_merged_prompt(code_root: str, files: List[str], separator: str = DEFAULT_SEPARATOR) -> Tuple[str, List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Returns:
      merged_text: concatenated prompt with [file] separators
      file_records: list of file metadata (segment_id, path, offsets)
      file_index: dict abs_path -> file metadata (same dict objects)
    """
    merged_parts: List[str] = []
    file_records: List[Dict[str, Any]] = []
    file_index: Dict[str, Dict[str, Any]] = {}

    base = os.path.abspath(os.path.join(os.path.abspath(code_root), os.pardir))

    cursor = 0
    for seg_id, abs_path in enumerate(files):
        display_path = _safe_relpath(abs_path, base).replace(os.path.sep, "/")
        header = f"{separator}\npath={display_path}\n\n"
        content = _read_file(abs_path)

        merged_parts.append(header)
        header_start = cursor
        content_start = cursor + len(header)
        cursor += len(header)

        merged_parts.append(content)
        content_end = cursor + len(content)
        cursor = content_end

        # Ensure a newline boundary between files (helps line mapping)
        if not content.endswith("\n"):
            merged_parts.append("\n")
            cursor += 1
            content_end += 1

        merged_parts.append("\n")  # extra blank line between files
        cursor += 1

        starts = _line_start_offsets(content if content.endswith("\n") else content + "\n")

        record = {
            "segment_id": seg_id,
            "abs_path": abs_path,
            "display_path": display_path,
            "header_start_char": header_start,
            "content_start_char": content_start,
            "content_end_char": content_end,
            "line_start_offsets": starts,  # relative to file content start
            "num_lines": len(starts),
        }
        file_records.append(record)
        file_index[abs_path] = record

    return "".join(merged_parts), file_records, file_index


def _resolve_report_path(report_path: Optional[str], code_root: str, all_files: List[str]) -> Optional[str]:
    """Resolve file identifiers used in reports to an absolute file path in `all_files`.

    The report may contain:
      - absolute paths
      - repo-relative paths (with ./ prefix)
      - module-like names without extension (e.g., 'alerts', 'ui', 'pkg.module')
      - short suffixes that match the tail of the real path
    """
    if not report_path:
        return None

    code_root_abs = os.path.abspath(code_root)

    # 1) Direct filesystem candidates
    candidates: List[str] = []
    if os.path.isabs(report_path):
        candidates.append(report_path)
    candidates.append(os.path.abspath(report_path))
    candidates.append(os.path.abspath(os.path.join(code_root_abs, report_path)))
    candidates.append(os.path.abspath(os.path.join(os.path.dirname(code_root_abs), report_path)))
    candidates.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(code_root_abs)), report_path)))

    # Try adding .py when report_path has no extension
    base = os.path.basename(report_path)
    if "." not in base:
        candidates.append(os.path.abspath(os.path.join(code_root_abs, report_path + ".py")))
        # module-like: a.b.c -> a/b/c.py
        candidates.append(os.path.abspath(os.path.join(code_root_abs, report_path.replace(".", os.path.sep) + ".py")))

    for c in candidates:
        if os.path.exists(c):
            # If this exact file is in all_files, return the canonical absolute path from all_files
            c_abs = os.path.abspath(c)
            if c_abs in all_files:
                return c_abs
            # Otherwise, accept it as-is
            return c_abs

    # 2) Match against enumerated files with scoring
    rp = str(report_path).replace("\\", "/").lstrip("./")
    rp_py = rp if rp.endswith(".py") else rp + ".py"
    rp_mod_py = rp.replace(".", "/")
    if not rp_mod_py.endswith(".py"):
        rp_mod_py += ".py"
    rp_base = os.path.splitext(os.path.basename(rp))[0]

    matches: List[Tuple[int, str]] = []

    for f in all_files:
        fp = f.replace("\\", "/")
        rel = os.path.relpath(f, code_root_abs).replace("\\", "/")
        rel_base = os.path.splitext(os.path.basename(rel))[0]

        # Strong matches first
        if fp.endswith(rp) or rel == rp or rel.endswith("/" + rp):
            matches.append((0, f))
            continue
        if fp.endswith(rp_py) or rel == rp_py or rel.endswith("/" + rp_py):
            matches.append((1, f))
            continue
        if fp.endswith(rp_mod_py) or rel == rp_mod_py or rel.endswith("/" + rp_mod_py):
            matches.append((2, f))
            continue

        # No-extension match on relpath without '.py'
        if rel.endswith(".py"):
            rel_no_ext = rel[:-3]
            if rel_no_ext == rp or rel_no_ext.endswith("/" + rp):
                matches.append((3, f))
                continue

        # Basename-only match (can be ambiguous; lowest priority)
        if rel_base == rp_base and rp_base:
            # Prefer shorter relpaths to reduce ambiguity
            matches.append((10 + rel.count("/"), f))

    if not matches:
        return None

    matches.sort(key=lambda x: x[0])
    return matches[0][1]

def _line_range_to_char_span(file_rec: Dict[str, Any], start_line: int, end_line: int) -> Tuple[int, int]:
    """
    Convert 1-indexed [start_line, end_line) to [start_char, end_char) in merged prompt.
    Assumes end_line is exclusive (same convention used by existing dataset_generator).
    """
    starts: List[int] = file_rec["line_start_offsets"]
    n = len(starts)
    # Clamp to valid range
    start_line = max(1, min(start_line, n))
    end_line = max(start_line, min(end_line, n + 1))

    start_rel = starts[start_line - 1]
    if end_line - 1 < n:
        end_rel = starts[end_line - 1]
    else:
        end_rel = file_rec["content_end_char"] - file_rec["content_start_char"]

    start_char = file_rec["content_start_char"] + start_rel
    end_char = file_rec["content_start_char"] + end_rel
    return start_char, end_char


def _collect_mentions_for_entry(entry: Dict[str, Any], code_root: str, all_files: List[str], file_by_abs: Dict[str, Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (anchor, mentions).
    - anchor is a dict or None
    - mentions is a list of dicts: {role, start_char, end_char, file_display_path, start_line, end_line}
    """
    mentions: List[Dict[str, Any]] = []

    file_path_raw = _get_value(entry, "file_path", "File")
    abs_primary = _resolve_report_path(file_path_raw, code_root, all_files) if file_path_raw else None
    primary_rec = file_by_abs.get(abs_primary) if abs_primary else None

    start_line = _get_value(entry, "start_line_number", "Start Line Number")
    end_line = _get_value(entry, "end_line_number", "End Line Number")

    anchor = None
    if primary_rec and start_line and end_line:
        a_start, a_end = _line_range_to_char_span(primary_rec, int(start_line), int(end_line))
        anchor = {
            "file": primary_rec["display_path"],
            "segment_id": primary_rec["segment_id"],
            "start_line": int(start_line),
            "end_line": int(end_line),
            "start_char": a_start,
            "end_char": a_end,
        }
        # Also include as a mention for maximum flexibility
        mentions.append({
            "role": "ANCHOR",
            "file": primary_rec["display_path"],
            "segment_id": primary_rec["segment_id"],
            "start_line": int(start_line),
            "end_line": int(end_line),
            "start_char": a_start,
            "end_char": a_end,
        })

    def add_list_spans(container: Any, role: str, abs_path: Optional[str]) -> None:
        if not container:
            return
        rec = file_by_abs.get(abs_path) if abs_path else None
        if not rec:
            return
        for span in container:
            s = _get_value(span, "start_line_number", "Start Line Number")
            e = _get_value(span, "end_line_number", "End Line Number")
            if not (s and e):
                continue
            s_i = int(s)
            e_i = int(e)
            c0, c1 = _line_range_to_char_span(rec, s_i, e_i)
            mentions.append({
                "role": role,
                "file": rec["display_path"],
                "segment_id": rec["segment_id"],
                "start_line": s_i,
                "end_line": e_i,
                "start_char": c0,
                "end_char": c1,
            })

    # Local multi-span evidence
    add_list_spans(_get_value(entry, "evidence_lines", "Evidence Lines") or [], "EVIDENCE_LINES", abs_primary)
    add_list_spans(_get_value(entry, "lines", "Lines") or [], "LINES", abs_primary)
    add_list_spans(_get_value(entry, "classes", "Classes") or [], "CLASSES", abs_primary)
    add_list_spans(_get_value(entry, "methods_functions", "Methods Functions") or [], "METHODS_FUNCTIONS", abs_primary)
    add_list_spans(_get_value(entry, "outgoing_evidence_lines", "Outgoing Evidence Lines") or [], "OUTGOING_EVIDENCE_LINES", abs_primary)

    # Cross-file evidence
    files = _get_value(entry, "files", "Files") or []
    for file_entry in files:
        other_raw = _get_value(file_entry, "name", "Name")
        abs_other = _resolve_report_path(other_raw, code_root, all_files) if other_raw else None
        incoming = _get_value(file_entry, "incoming_evidence_lines", "Incoming Evidence Lines") or []
        inst = _get_value(file_entry, "evidence_lines", "Evidence Lines") or []
        if incoming:
            add_list_spans(incoming, "INCOMING_EVIDENCE_LINES", abs_other)
        if inst:
            add_list_spans(inst, "RELATED_EVIDENCE_LINES", abs_other)

    return anchor, mentions


def build_detr_dataset(code_root: str, report_path: str, output_path: str, separator: str = DEFAULT_SEPARATOR) -> Dict[str, Any]:
    code_root_abs = os.path.abspath(code_root)
    all_files = sorted(_iter_code_files(code_root_abs))
    report_entries = _load_json(report_path)

    merged_text, file_records, file_by_abs = _build_merged_prompt(code_root_abs, all_files, separator=separator)

    Evidences: List[Dict[str, Any]] = []
    dropped = 0
    for idx, entry in enumerate(report_entries):
        smell_name = _get_value(entry, "name", "Name")
        if not smell_name:
            continue

        anchor, mentions = _collect_mentions_for_entry(entry, code_root_abs, all_files, file_by_abs)
        if not mentions:
            dropped += 1
            continue

        inst = {
            "id": idx,
            "category": _get_value(entry, "type", "Type"),
            "smell_name": smell_name,
            "severity": _get_value(entry, "severity", "Severity"),
            "description": _get_value(entry, "description", "Description"),
            "primary_file": _get_value(entry, "file_path", "File"),
            "anchor": anchor,
            "mentions": mentions,
        }
        Evidences.append(inst)

    schema = {
        "separator_token": separator,
        "mention_roles": sorted({m["role"] for inst in Evidences for m in inst["mentions"]}),
        "num_Evidences": len(Evidences),
        "dropped_Evidences_without_resolved_spans": dropped,
    }

    out_obj = {
        "sample_id": os.path.basename(os.path.normpath(code_root_abs)),
        "code_root": code_root_abs,
        "text": merged_text,
        "files": [
            {
                "segment_id": r["segment_id"],
                "path": r["display_path"],
                "content_start_char": r["content_start_char"],
                "content_end_char": r["content_end_char"],
                "num_lines": r["num_lines"],
            }
            for r in file_records
        ],
        "Evidences": Evidences,
        "schema": schema,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)

    # also write a sidecar schema for quick inspection
    schema_path = os.path.splitext(output_path)[0] + ".schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    return out_obj


def _default_output_path(code_path: str) -> str:
    candidate = os.path.abspath(code_path)
    if os.path.isfile(candidate) or candidate.endswith(".py"):
        candidate = os.path.dirname(candidate)
    base_name = os.path.basename(os.path.normpath(candidate)) or "code"
    outdir = f"dataset_{base_name}"
    return os.path.join(outdir, "detr_dataset.json")


def main():
    parser = argparse.ArgumentParser(
        description="Build a DETR-style dataset (set of smell Evidences with explicit spans) from a PyExamine report."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--report", required=True, help="Path to code_quality_report.json")
    parser.add_argument("--output", default=None, help="Output JSON path (default: dataset_<code>/detr_dataset.json)")
    parser.add_argument("--separator", default=DEFAULT_SEPARATOR, help="Separator token to place between files (default: [file])")
    args = parser.parse_args()

    output_path = args.output or _default_output_path(args.code_path)
    build_detr_dataset(args.code_path, args.report, output_path, separator=args.separator)


if __name__ == "__main__":
    main()

