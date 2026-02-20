import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _to_abs_path(code_root: str, maybe_rel_path: Optional[str]) -> Optional[str]:
    if not maybe_rel_path:
        return None
    norm = maybe_rel_path.replace("\\", "/")
    if os.path.isabs(norm):
        return norm
    return os.path.abspath(os.path.join(code_root, norm))


def _read_lines_cached(path: str, cache: Dict[str, List[str]]) -> List[str]:
    if path not in cache:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            cache[path] = f.readlines()
    return cache[path]


def _slice_lines(lines: List[str], start_line: int, end_line: int) -> str:
    # DETR spans use 1-indexed [start_line, end_line) convention.
    s = max(1, int(start_line))
    e = max(s, int(end_line))
    return "".join(lines[s - 1 : e - 1])


def _extract_excerpt_text(
    code_root: str,
    mention: Dict[str, Any],
    line_cache: Dict[str, List[str]],
) -> Tuple[str, bool, Optional[str]]:
    file_path = mention.get("file")
    abs_path = _to_abs_path(code_root, file_path)
    if not abs_path:
        return "", False, None
    try:
        lines = _read_lines_cached(abs_path, line_cache)
        text = _slice_lines(
            lines,
            int(mention.get("start_line", 1) or 1),
            int(mention.get("end_line", 1) or 1),
        )
        return text, True, abs_path
    except OSError:
        return "", False, abs_path


def _sort_mentions(mentions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        mentions,
        key=lambda m: (
            str(m.get("file", "")),
            int(m.get("start_line", 0) or 0),
            int(m.get("start_char", 0) or 0),
            int(m.get("end_line", 0) or 0),
            int(m.get("end_char", 0) or 0),
            str(m.get("role", "")),
        ),
    )


def build_excerpts(detr_path: str, output_path: str) -> Dict[str, Any]:
    detr = _load_json(detr_path)
    code_root = detr.get("code_root") or os.getcwd()
    evidences = detr.get("Evidences", [])

    line_cache: Dict[str, List[str]] = {}
    excerpt_sets: List[Dict[str, Any]] = []

    for ev in evidences:
        evidence_id = ev.get("id")
        smell_name = ev.get("smell_name")
        mentions = _sort_mentions(ev.get("mentions", []))

        excerpts: List[Dict[str, Any]] = []
        for idx, mention in enumerate(mentions):
            text, resolved, abs_path = _extract_excerpt_text(code_root, mention, line_cache)
            source_roles = mention.get("source_roles")
            if not isinstance(source_roles, list):
                source_roles = [mention.get("role")] if mention.get("role") else []

            excerpt_id = f"ev_{evidence_id}_ex_{idx}"
            path_tag = f"{mention.get('file')}#L{mention.get('start_line')}-{mention.get('end_line')}"
            block = (
                "[path]\n"
                f"path={path_tag}\n"
                "<contents>\n"
                f"{text}"
            )

            excerpts.append(
                {
                    "excerpt_id": excerpt_id,
                    "role": mention.get("role"),
                    "source_roles": source_roles,
                    "path": mention.get("file"),
                    "abs_path": abs_path,
                    "segment_id": mention.get("segment_id"),
                    "start_line": mention.get("start_line"),
                    "end_line": mention.get("end_line"),
                    "start_char": mention.get("start_char"),
                    "end_char": mention.get("end_char"),
                    "resolved": resolved,
                    "text": text,
                    "formatted_block": block,
                }
            )

        excerpt_sets.append(
            {
                "set_id": f"ev_{evidence_id}",
                "evidence_id": evidence_id,
                "smell_name": smell_name,
                "category": ev.get("category"),
                "severity": ev.get("severity"),
                "anchor": ev.get("anchor"),
                "has_resolved_mentions": ev.get("has_resolved_mentions"),
                "num_excerpts": len(excerpts),
                "excerpts": excerpts,
            }
        )

    out = {
        "sample_id": detr.get("sample_id"),
        "code_root": code_root,
        "source_detr": os.path.abspath(detr_path),
        "schema_version": "excerpt_set_v1",
        "num_excerpt_sets": len(excerpt_sets),
        "excerpt_sets": excerpt_sets,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return out


def _default_output_path(detr_path: str) -> str:
    base, _ = os.path.splitext(os.path.abspath(detr_path))
    return base + "_excerpts.json"


def main():
    parser = argparse.ArgumentParser(description="Build excerpt sets from DETR-style evidence JSON.")
    parser.add_argument("--detr", required=True, help="Path to DETR JSON (e.g., code_quality_report_detr.json)")
    parser.add_argument("--output", default=None, help="Output path (default: <detr>_excerpts.json)")
    args = parser.parse_args()

    output_path = args.output or _default_output_path(args.detr)
    build_excerpts(args.detr, output_path)


if __name__ == "__main__":
    main()
