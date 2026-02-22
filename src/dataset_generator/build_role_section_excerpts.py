import argparse
import ast
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .token_label_selectors import select_positive_indices

@dataclass(frozen=True)
class Span:
    file_path: str
    start_line: int
    end_line: int  # exclusive


@dataclass(frozen=True)
class Candidate:
    smell_name: str
    key: Tuple
    entry: Dict
    is_detected: bool


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_jsonl(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str, rows: List[Dict]):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _get_value(entry: Dict, *keys):
    for key in keys:
        if key in entry:
            return entry[key]
    return None


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    return " ".join(str(name).strip().split())


def _normalize_path(path: Optional[str], code_root: str) -> Optional[str]:
    if not path:
        return None
    path = str(path)
    if os.path.isabs(path) and os.path.exists(path):
        return os.path.abspath(path)
    if os.path.exists(path):
        return os.path.abspath(path)
    candidate = os.path.abspath(os.path.join(code_root, path))
    if os.path.exists(candidate):
        return candidate
    # Per-project runs can emit paths relative to the parent of code_root
    # (e.g., "project/file.py" while code_root is ".../samples/project").
    parent_candidate = os.path.abspath(os.path.join(os.path.dirname(code_root), path))
    if os.path.exists(parent_candidate):
        return parent_candidate
    module_candidate = os.path.abspath(
        os.path.join(code_root, path.replace(".", os.path.sep) + ".py")
    )
    if os.path.exists(module_candidate):
        return module_candidate
    return None


def _display_path(abs_path: str, code_root: str) -> str:
    samples_root = os.path.abspath(os.path.join(code_root, os.pardir))
    try:
        common_root = os.path.commonpath([samples_root, abs_path])
    except ValueError:
        common_root = ""
    if common_root == samples_root:
        return os.path.relpath(abs_path, samples_root).replace("\\", "/")
    return abs_path.replace("\\", "/")


def _iter_code_files(root_path: str):
    if os.path.isfile(root_path):
        if root_path.endswith(".py"):
            yield os.path.abspath(root_path)
        return
    for root, _, files in os.walk(root_path):
        for name in files:
            if name.endswith(".py"):
                yield os.path.abspath(os.path.join(root, name))


def _read_file(path: str) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp949"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as handle:
                return handle.read()
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _line_count(path: str) -> int:
    return len(_read_file(path).splitlines())


def _parse_symbols(code_root: str):
    classes = []
    functions = []
    files = []
    for file_path in sorted(_iter_code_files(code_root)):
        files.append(file_path)
        content = _read_file(file_path)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(
                    {
                        "file_path": file_path,
                        "class_name": node.name,
                        "start_line_number": node.lineno,
                        "end_line_number": (getattr(node, "end_lineno", node.lineno) + 1),
                    }
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(
                    {
                        "file_path": file_path,
                        "method/function": node.name,
                        "function": node.name,
                        "start_line_number": node.lineno,
                        "end_line_number": (getattr(node, "end_lineno", node.lineno) + 1),
                    }
                )
    return {"classes": classes, "functions": functions, "files": files}


def _candidate_key(smell_name: str, entry: Dict, code_root: str) -> Tuple:
    file_path = _normalize_path(_get_value(entry, "file_path", "File"), code_root)
    class_name = _get_value(entry, "class_name", "Class")
    method_name = _get_value(entry, "method/function", "Method/Function", "function", "Function")
    start = _get_value(entry, "start_line_number", "Start Line Number")
    end = _get_value(entry, "end_line_number", "End Line Number")
    files = _get_value(entry, "files", "Files") or []
    file_set = []
    for item in files:
        name = _normalize_path(_get_value(item, "name", "Name"), code_root)
        if name:
            file_set.append(name)
    if class_name:
        return (smell_name, "class", file_path, class_name, start, end)
    if method_name:
        return (smell_name, "method", file_path, method_name, start, end)
    if file_path:
        return (smell_name, "file", file_path, start, end)
    if file_set:
        return (smell_name, "files", tuple(sorted(file_set)))
    return (smell_name, "row-hash", json.dumps(entry, sort_keys=True))


def _build_detected_candidates(report_rows: List[Dict], code_root: str):
    detected = {}
    for row in report_rows:
        smell_name = _normalize_name(_get_value(row, "name", "Name"))
        if not smell_name:
            continue
        key = _candidate_key(smell_name, row, code_root)
        if key not in detected:
            detected[key] = row
    return detected


def _template_map(templates: List[Dict]) -> Dict[str, Dict]:
    return {_normalize_name(t["name"]): t for t in templates}


def _derive_universe_for_smell(smell_name: str, template: Dict, symbols: Dict, code_root: str):
    universe = []
    role0_specs = template.get("ROLE0", [])
    role0_line_source = role0_specs[0]["line_source"] if role0_specs else ""
    has_class = "class_name" in template
    has_method = ("method/function" in template) or ("function" in template)
    has_root_lines = "start_line_number" in template and "end_line_number" in template
    has_file = "file_path" in template

    # ROLE0-driven synthesis for templates that rely on child arrays.
    if role0_line_source.startswith("classes[*]"):
        by_file: Dict[str, List[Dict]] = {}
        for cls in symbols["classes"]:
            by_file.setdefault(cls["file_path"], []).append(cls)
        for file_path, items in by_file.items():
            if len(items) < 2:
                continue
            classes = []
            for item in sorted(items, key=lambda x: (x["start_line_number"], x["class_name"])):
                classes.append(
                    {
                        "name": item["class_name"],
                        "start_line_number": item["start_line_number"],
                        "end_line_number": item["end_line_number"],
                    }
                )
            universe.append(
                {
                    "name": smell_name,
                    "file_path": _display_path(file_path, code_root),
                    "classes": classes,
                }
            )
        return universe

    if role0_line_source.startswith("methods/functions[*]"):
        by_file: Dict[str, List[Dict]] = {}
        for fn in symbols["functions"]:
            by_file.setdefault(fn["file_path"], []).append(fn)
        for file_path, items in by_file.items():
            if len(items) < 2:
                continue
            methods = []
            for item in sorted(items, key=lambda x: (x["start_line_number"], x["method/function"])):
                methods.append(
                    {
                        "name": item["method/function"],
                        "start_line_number": item["start_line_number"],
                        "end_line_number": item["end_line_number"],
                    }
                )
            universe.append(
                {
                    "name": smell_name,
                    "file_path": _display_path(file_path, code_root),
                    "methods/functions": methods,
                }
            )
        return universe

    if role0_line_source in {"lines[*].start_line_number/end_line_number", "evidence_lines[*].start_line_number/end_line_number"}:
        key = "lines" if role0_line_source.startswith("lines[*]") else "evidence_lines"
        for fp in symbols["files"]:
            total_lines = _line_count(fp)
            universe.append(
                {
                    "name": smell_name,
                    "file_path": _display_path(fp, code_root),
                    key: [{"start_line_number": 1, "end_line_number": total_lines + 1}],
                }
            )
        return universe

    if role0_line_source.startswith("files[*]."):
        child_key = role0_line_source[len("files[*].") :].split("[*].")[0]
        if child_key not in {"evidence_lines", "instance_lines", "incoming_evidence_lines", "incoming_instance_lines"}:
            child_key = "evidence_lines"
        for fp in symbols["files"]:
            total_lines = _line_count(fp)
            file_display = _display_path(fp, code_root)
            universe.append(
                {
                    "name": smell_name,
                    "files": [
                        {
                            "name": file_display,
                            child_key: [{"start_line_number": 1, "end_line_number": total_lines + 1}],
                        }
                    ],
                }
            )
        return universe

    if role0_line_source == "WHOLE_FILE":
        for fp in symbols["files"]:
            universe.append({"name": smell_name, "file_path": _display_path(fp, code_root)})
        return universe

    if has_method:
        for fn in symbols["functions"]:
            entry = {
                "name": smell_name,
                "file_path": _display_path(fn["file_path"], code_root),
                "start_line_number": fn["start_line_number"],
                "end_line_number": fn["end_line_number"],
                "method/function": fn["method/function"],
                "function": fn["function"],
            }
            universe.append(entry)
        return universe

    if has_class:
        for cls in symbols["classes"]:
            entry = {
                "name": smell_name,
                "file_path": _display_path(cls["file_path"], code_root),
                "class_name": cls["class_name"],
                "start_line_number": cls["start_line_number"],
                "end_line_number": cls["end_line_number"],
            }
            universe.append(entry)
        return universe

    if has_file or has_root_lines:
        for fp in symbols["files"]:
            total_lines = _line_count(fp)
            entry = {"name": smell_name, "file_path": _display_path(fp, code_root)}
            if has_root_lines:
                entry["start_line_number"] = 1
                entry["end_line_number"] = total_lines + 1
            universe.append(entry)
        return universe

    # Multi-file/project-like fallback: file-level candidates to create undetected instances.
    for fp in symbols["files"]:
        universe.append({"name": smell_name, "file_path": _display_path(fp, code_root)})
    return universe


def _resolve_line_items(entry: Dict, line_source: str):
    # Returns list of (start,end,container)
    out = []
    if line_source == "start_line_number/end_line_number":
        s = _get_value(entry, "start_line_number", "Start Line Number")
        e = _get_value(entry, "end_line_number", "End Line Number")
        if s and e:
            out.append((int(s), int(e), entry))
        return out
    if line_source == "WHOLE_FILE":
        return [("WHOLE_FILE", "WHOLE_FILE", entry)]

    if line_source.startswith("files[*]."):
        key = line_source[len("files[*].") :]
        key = key.split("[*].")[0]
        for child in _get_value(entry, "files", "Files") or []:
            line_list = (
                _get_value(child, key, key.title().replace("_", " "))
                or _get_value(child, "instance_lines", "Instance Lines")
                or _get_value(child, "incoming_instance_lines", "Incoming Instance Lines")
                or _get_value(child, "evidence_lines", "Evidence Lines")
                or []
            )
            for span in line_list:
                s = _get_value(span, "start_line_number", "Start Line Number")
                e = _get_value(span, "end_line_number", "End Line Number")
                if s and e:
                    out.append((int(s), int(e), child))
        return out

    key = line_source.split("[*].")[0]
    line_list = (
        _get_value(entry, key, key.title().replace("_", " "))
        or _get_value(entry, "instance_lines", "Instance Lines")
        or _get_value(entry, "evidence_lines", "Evidence Lines")
        or _get_value(entry, "lines", "Lines")
        or _get_value(entry, "methods/functions", "Methods/Functions")
        or _get_value(entry, "classes", "Classes")
        or []
    )
    for span in line_list:
        s = _get_value(span, "start_line_number", "Start Line Number")
        e = _get_value(span, "end_line_number", "End Line Number")
        if s and e:
            out.append((int(s), int(e), entry))
    return out


def _resolve_file_for_item(entry: Dict, item_container: Dict, file_source: str, code_root: str) -> Optional[str]:
    if file_source == "file_path":
        return _normalize_path(_get_value(entry, "file_path", "File"), code_root)
    if file_source == "files[*].name":
        return _normalize_path(_get_value(item_container, "name", "Name"), code_root)
    return None


def _collect_role_spans(entry: Dict, role_specs: List[Dict], code_root: str) -> List[Span]:
    spans = []
    for spec in role_specs:
        line_source = spec.get("line_source")
        file_source = spec.get("file_source")
        if not line_source or not file_source:
            continue
        for start, end, container in _resolve_line_items(entry, line_source):
            abs_path = _resolve_file_for_item(entry, container, file_source, code_root)
            if not abs_path:
                continue
            if start == "WHOLE_FILE":
                total = _line_count(abs_path)
                spans.append(Span(abs_path, 1, total + 1))
            else:
                spans.append(Span(abs_path, max(1, int(start)), max(int(start) + 1, int(end))))
    return spans


def _fallback_role_spans(
    entry: Dict,
    role_specs: List[Dict],
    code_root: str,
    role0_spans: List[Span],
) -> List[Span]:
    # Deterministic fallback used when template expects a role but the entry lacks explicit evidence arrays.
    fallback = []
    root_path = _normalize_path(_get_value(entry, "file_path", "File"), code_root)
    root_start = _get_value(entry, "start_line_number", "Start Line Number")
    root_end = _get_value(entry, "end_line_number", "End Line Number")

    def _root_span():
        if root_path and root_start and root_end:
            return Span(root_path, max(1, int(root_start)), max(int(root_start) + 1, int(root_end)))
        return None

    for spec in role_specs:
        line_source = spec.get("line_source", "")
        file_source = spec.get("file_source", "")

        if file_source == "file_path":
            if line_source == "WHOLE_FILE":
                if root_path:
                    fallback.append(Span(root_path, 1, _line_count(root_path) + 1))
                else:
                    files = _get_value(entry, "files", "Files") or []
                    for child in files:
                        cp = _normalize_path(_get_value(child, "name", "Name"), code_root)
                        if cp:
                            fallback.append(Span(cp, 1, _line_count(cp) + 1))
                            break
                continue
            base = _root_span()
            if base:
                fallback.append(base)
            elif root_path:
                fallback.append(Span(root_path, 1, _line_count(root_path) + 1))
            else:
                files = _get_value(entry, "files", "Files") or []
                for child in files:
                    cp = _normalize_path(_get_value(child, "name", "Name"), code_root)
                    if cp:
                        fallback.append(Span(cp, 1, _line_count(cp) + 1))
                        break
            if role0_spans and not fallback:
                fallback.extend(role0_spans)
            continue

        if file_source == "files[*].name":
            files = _get_value(entry, "files", "Files") or []
            child_paths = []
            for child in files:
                cp = _normalize_path(_get_value(child, "name", "Name"), code_root)
                if cp:
                    child_paths.append(cp)
            # If no explicit children exist, reuse root path so ROLE section is still materialized.
            if not child_paths and root_path:
                child_paths.append(root_path)
            for cp in child_paths:
                if line_source == "WHOLE_FILE":
                    fallback.append(Span(cp, 1, _line_count(cp) + 1))
                else:
                    # Prefer root range as a compact fallback; otherwise whole file.
                    if root_start and root_end:
                        fallback.append(
                            Span(cp, max(1, int(root_start)), max(int(root_start) + 1, int(root_end)))
                        )
                    else:
                        fallback.append(Span(cp, 1, _line_count(cp) + 1))
            continue

    if not fallback and role0_spans:
        fallback.extend(role0_spans)
    return fallback


def _expand_and_merge(spans: List[Span], context_lines: int, file_cache: Dict[str, List[str]]) -> List[Span]:
    grouped: Dict[str, List[Tuple[int, int]]] = {}
    for span in spans:
        grouped.setdefault(span.file_path, []).append((span.start_line, span.end_line))
    merged_spans = []
    for file_path, ranges in grouped.items():
        total = len(file_cache[file_path])
        expanded = []
        for s, e in ranges:
            start = max(1, s - context_lines)
            end = min(total + 1, e + context_lines)
            expanded.append((start, end))
        expanded.sort()
        merged = []
        for s, e in expanded:
            if not merged:
                merged.append([s, e])
                continue
            if s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        for s, e in merged:
            merged_spans.append(Span(file_path, s, e))
    merged_spans.sort(key=lambda x: (x.file_path, x.start_line, x.end_line))
    return merged_spans


def _render_role_section(role_name: str, spans: List[Span], code_root: str, file_cache: Dict[str, List[str]]):
    chunks = [f"[{role_name}]"]
    segment_meta = []
    for span in spans:
        display = _display_path(span.file_path, code_root)
        lines = file_cache[span.file_path][span.start_line - 1 : span.end_line - 1]
        excerpt = "".join(lines)
        if excerpt and not excerpt.endswith("\n"):
            excerpt += "\n"
        chunks.append("[FILE]")
        chunks.append(f"path={display}")
        chunks.append(excerpt.rstrip("\n"))
        chunks.append("[SEP_EXCERPT]")
        segment_meta.append(
            {
                "role": role_name,
                "file_path": display,
                "source_line_start": span.start_line,
                "source_line_end_exclusive": span.end_line,
            }
        )
    if not spans:
        chunks.append("")
    text = "\n".join(chunks) + "\n\n"
    return text, segment_meta


_TOKEN_RE = re.compile(r"\S+")


def _char_to_source(file_path: str, start_line: int, excerpt_text: str, token_rel_start: int, token_rel_end: int):
    # Build quick line offsets for this excerpt
    line_offsets = [0]
    for i, ch in enumerate(excerpt_text):
        if ch == "\n":
            line_offsets.append(i + 1)
    # token start line
    line_idx = 0
    while line_idx + 1 < len(line_offsets) and line_offsets[line_idx + 1] <= token_rel_start:
        line_idx += 1
    line_start_char = line_offsets[line_idx]
    token_start_col = token_rel_start - line_start_char

    end_idx = line_idx
    while end_idx + 1 < len(line_offsets) and line_offsets[end_idx + 1] <= token_rel_end:
        end_idx += 1
    end_line_start_char = line_offsets[end_idx]
    token_end_col = token_rel_end - end_line_start_char

    return {
        "source_line_start": start_line + line_idx,
        "source_col_start": token_start_col,
        "source_line_end": start_line + end_idx,
        "source_col_end": token_end_col,
    }


def _line_in_ranges(
    line_no: int, ranges: List[Tuple[int, int, int]]
) -> Optional[Tuple[int, int, int]]:
    for s, e, entry_id in ranges:
        if s <= line_no < e:
            return (s, e, entry_id)
    return None


def _tokenize_with_sidecar(text: str, code_blocks: List[Dict]):
    # code_blocks: [{role, file_path, source_line_start, text_start, text_end, source_span_start_line, source_span_end_line}]
    tokens = []
    labels = []
    token_map = []
    prev_positive = {"role": None, "file_path": None, "range": None}
    for idx, match in enumerate(_TOKEN_RE.finditer(text)):
        tok = match.group(0)
        start = match.start()
        end = match.end()
        block = None
        for cb in code_blocks:
            if cb["text_start"] <= start < cb["text_end"]:
                block = cb
                break
        is_structural = block is None
        tokens.append(tok)
        if is_structural:
            labels.append(-100)
            token_map.append(
                {
                    "token_idx": idx,
                    "token": tok,
                    "start": start,
                    "end": end,
                    "is_structural": True,
                }
            )
            continue

        rel_start = start - block["text_start"]
        rel_end = end - block["text_start"]
        src = _char_to_source(
            block["file_path_abs"],
            block["source_line_start"],
            block["excerpt_text"],
            rel_start,
            rel_end,
        )
        token_line = src["source_line_start"]
        line_range = _line_in_ranges(token_line, block.get("exact_ranges", []))
        if line_range is None:
            label = "O"
            prev_positive = {"role": None, "file_path": None, "range": None}
        else:
            if (
                prev_positive["role"] == block["role"]
                and prev_positive["file_path"] == block["file_path"]
                and prev_positive["range"] == line_range
            ):
                label = f'I-{block["role"]}'
            else:
                label = f'B-{block["role"]}'
            prev_positive = {
                "role": block["role"],
                "file_path": block["file_path"],
                "range": line_range,
            }
        labels.append(label)
        token_map.append(
            {
                "token_idx": idx,
                "token": tok,
                "start": start,
                "end": end,
                "is_structural": False,
                "role": block["role"],
                "label": label,
                "file_path": block["file_path"],
                **src,
                "source_span_start_line": block["source_span_start_line"],
                "source_span_end_line": block["source_span_end_line"],
            }
        )
    return tokens, labels, token_map


def _apply_token_granularity(
    smell_name: str,
    entry: Dict,
    tokens: List[str],
    line_labels: List,
    token_map: List[Dict],
) -> Tuple[List, List[Dict], bool]:
    labels = []
    for lbl in line_labels:
        if lbl == -100:
            labels.append(-100)
        else:
            labels.append("O")

    def _entry_groups(role: str) -> List[List[int]]:
        groups: List[List[int]] = []
        current: List[int] = []
        b_tag = f"B-{role}"
        i_tag = f"I-{role}"
        for i, lbl in enumerate(line_labels):
            if lbl == b_tag:
                if current:
                    groups.append(current)
                current = [i]
            elif lbl == i_tag:
                if not current:
                    # Defensive: malformed BIO; start new group.
                    current = [i]
                else:
                    current.append(i)
            else:
                if current:
                    groups.append(current)
                    current = []
        if current:
            groups.append(current)
        return groups

    fallbacks: List[Dict] = []
    any_fallback = False
    for role in ("ROLE0", "ROLE1", "ROLE2"):
        groups = _entry_groups(role)
        for entry_idx, candidate_indices in enumerate(groups):
            selected = select_positive_indices(
                smell_name=smell_name,
                role=role,
                tokens=tokens,
                token_map=token_map,
                candidate_indices=candidate_indices,
                entry=entry,
            )

            # Safety fallback: if selector yields nothing for this role entry,
            # keep line-level BIO labels for that entry.
            if not selected:
                any_fallback = True
                fallbacks.append(
                    {
                        "role": role,
                        "entry_index": entry_idx,
                        "applied": "line",
                        "reason": "selector_empty",
                    }
                )
                for idx in candidate_indices:
                    labels[idx] = line_labels[idx]
                continue

            prev = None
            for idx in sorted(selected):
                if prev is not None and idx == prev + 1:
                    labels[idx] = f"I-{role}"
                else:
                    labels[idx] = f"B-{role}"
                prev = idx

    return labels, fallbacks, any_fallback


def _build_text_and_sidecar(
    role_spans: Dict[str, List[Span]],
    role_exact_spans: Dict[str, List[Span]],
    smell_name: str,
    entry: Dict,
    label_granularity: str,
    code_root: str,
    file_cache: Dict[str, List[str]],
):
    text_parts = []
    segments = []
    code_blocks = []
    cursor = 0

    for role in ("ROLE0", "ROLE1", "ROLE2"):
        spans = role_spans.get(role, [])
        section_text, section_meta = _render_role_section(role, spans, code_root, file_cache)
        text_parts.append(section_text)
        for meta in section_meta:
            segments.append(meta)

    text = "".join(text_parts)

    # Index exact (non-context) ranges for BIO/O labels.
    exact_index: Dict[str, Dict[str, List[Tuple[int, int, int]]]] = {}
    for role in ("ROLE0", "ROLE1", "ROLE2"):
        by_file: Dict[str, List[Tuple[int, int, int]]] = {}
        for entry_id, span in enumerate(role_exact_spans.get(role, [])):
            display = _display_path(span.file_path, code_root)
            by_file.setdefault(display, []).append((span.start_line, span.end_line, entry_id))
        exact_index[role] = by_file

    # Re-scan text and identify code ranges by parsing deterministic markers.
    role = None
    i = 0
    while i < len(text):
        if text.startswith("[ROLE0]\n", i):
            role = "ROLE0"
            i += len("[ROLE0]\n")
            continue
        if text.startswith("[ROLE1]\n", i):
            role = "ROLE1"
            i += len("[ROLE1]\n")
            continue
        if text.startswith("[ROLE2]\n", i):
            role = "ROLE2"
            i += len("[ROLE2]\n")
            continue
        if text.startswith("[FILE]\npath=", i):
            path_start = i + len("[FILE]\npath=")
            path_end = text.find("\n", path_start)
            if path_end < 0:
                break
            path = text[path_start:path_end]
            code_start = path_end + 1
            sep = text.find("\n[SEP_EXCERPT]\n", code_start)
            if sep < 0:
                break
            code_end = sep
            abs_path = _normalize_path(path, code_root)
            # Match span from segments list in order
            segment = None
            for seg in segments:
                if seg["role"] == role and seg["file_path"] == path:
                    # first unmatched
                    if not seg.get("_used"):
                        segment = seg
                        seg["_used"] = True
                        break
            if abs_path and segment:
                code_blocks.append(
                    {
                        "role": role,
                        "file_path": path,
                        "file_path_abs": abs_path,
                        "source_line_start": segment["source_line_start"],
                        "source_span_start_line": segment["source_line_start"],
                        "source_span_end_line": segment["source_line_end_exclusive"],
                        "text_start": code_start,
                        "text_end": code_end,
                        "excerpt_text": text[code_start:code_end],
                        "exact_ranges": exact_index.get(role, {}).get(path, []),
                    }
                )
            i = sep + len("\n[SEP_EXCERPT]\n")
            continue
        i += 1

    tokens, labels, token_map = _tokenize_with_sidecar(text, code_blocks)
    fallbacks: List[Dict] = []
    fallback_used = False
    if label_granularity == "token":
        labels, fallbacks, fallback_used = _apply_token_granularity(
            smell_name, entry, tokens, labels, token_map
        )
    return text, tokens, labels, token_map, fallbacks, fallback_used


def build_role_section_excerpts(
    code_path: str,
    report_path: str,
    templates_path: str,
    output_jsonl: str,
    output_sidecar_jsonl: str,
    context_lines: int = 2,
    label_granularity: str = "line",
):
    code_root = os.path.abspath(code_path)
    report_rows = _load_json(report_path)
    templates = _load_json(templates_path)
    smell_template = _template_map(templates)
    symbols = _parse_symbols(code_root)
    detected_map = _build_detected_candidates(report_rows, code_root)
    detected_keys = set(detected_map.keys())

    file_cache = {fp: _read_file(fp).splitlines(keepends=True) for fp in symbols["files"]}

    candidates: List[Candidate] = []
    for smell_name, template in sorted(smell_template.items()):
        universe_entries = _derive_universe_for_smell(smell_name, template, symbols, code_root)
        seen_keys = set()
        for entry in universe_entries:
            key = _candidate_key(smell_name, entry, code_root)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if key in detected_map:
                row = dict(detected_map[key])
                candidates.append(Candidate(smell_name, key, row, True))
            else:
                candidates.append(Candidate(smell_name, key, entry, False))
        # Ensure all detected rows are covered even if universe misses them.
        for key, row in detected_map.items():
            if key[0] != smell_name or key in seen_keys:
                continue
            candidates.append(Candidate(smell_name, key, dict(row), True))

    out_rows = []
    sidecar_rows = []
    row_id = 0

    for cand in candidates:
        template = smell_template.get(cand.smell_name)
        if not template:
            continue
        role_spans = {}
        role_exact_spans = {}
        role0_expanded = []
        for role in ("ROLE0", "ROLE1", "ROLE2"):
            specs = template.get(role, [])
            raw_spans = _collect_role_spans(cand.entry, specs, code_root)
            raw_spans = [s for s in raw_spans if s.file_path in file_cache]
            # Keep exact spans unmerged to preserve evidence-entry identity.
            exact = list(raw_spans)
            role_exact_spans[role] = exact
            if specs and not raw_spans:
                raw_spans = _fallback_role_spans(cand.entry, specs, code_root, role0_expanded)
                raw_spans = [s for s in raw_spans if s.file_path in file_cache]
            merged = _expand_and_merge(raw_spans, context_lines=context_lines, file_cache=file_cache)
            role_spans[role] = merged
            if role == "ROLE0":
                role0_expanded = merged

        text, tokens, labels, token_map, fallbacks, fallback_used = _build_text_and_sidecar(
            role_spans,
            role_exact_spans,
            cand.smell_name,
            cand.entry,
            label_granularity,
            code_root,
            file_cache,
        )
        requested_granularity = label_granularity
        effective_granularity = (
            "line" if (requested_granularity == "token" and fallback_used) else requested_granularity
        )

        out_rows.append(
            {
                "id": row_id,
                "smell_name": cand.smell_name,
                "is_detected": cand.is_detected,
                "label_granularity": effective_granularity,
                "requested_label_granularity": requested_granularity,
                "effective_label_granularity": effective_granularity,
                "granularity_fallbacks": fallbacks,
                "text": text,
                "tokens": tokens,
                "labels": labels,
            }
        )
        sidecar_rows.append(
            {
                "id": row_id,
                "smell_name": cand.smell_name,
                "is_detected": cand.is_detected,
                "label_granularity": effective_granularity,
                "requested_label_granularity": requested_granularity,
                "effective_label_granularity": effective_granularity,
                "granularity_fallbacks": fallbacks,
                "tokenization_backend": "regex-fallback",
                "token_map": token_map,
            }
        )
        row_id += 1

    _write_jsonl(output_jsonl, out_rows)
    _write_jsonl(output_sidecar_jsonl, sidecar_rows)

    return {
        "rows": len(out_rows),
        "detected_rows": sum(1 for x in out_rows if x["is_detected"]),
        "undetected_rows": sum(1 for x in out_rows if not x["is_detected"]),
        "detected_keys": len(detected_keys),
        "label_granularity": label_granularity,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build role-section excerpts and sidecar JSONL from code/report/templates."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--report", required=True, help="Path to code_quality_report.json")
    parser.add_argument(
        "--templates",
        default="master-thesis-materials/data/templates_with_roles.json",
        help="Path to templates_with_roles.json",
    )
    parser.add_argument(
        "--output-jsonl",
        default="role_section_excerpts.jsonl",
        help="Path to output JSONL with text/tokens/labels.",
    )
    parser.add_argument(
        "--output-sidecar-jsonl",
        default="role_section_excerpts.sidecar.jsonl",
        help="Path to output sidecar JSONL.",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=2,
        help="Context lines to include before/after each span.",
    )
    parser.add_argument(
        "--label-granularity",
        choices=["line", "token"],
        default="line",
        help="Labeling granularity metadata written to outputs.",
    )
    args = parser.parse_args()

    stats = build_role_section_excerpts(
        code_path=args.code_path,
        report_path=args.report,
        templates_path=args.templates,
        output_jsonl=args.output_jsonl,
        output_sidecar_jsonl=args.output_sidecar_jsonl,
        context_lines=max(0, args.context_lines),
        label_granularity=args.label_granularity,
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
