from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .build_module_complexity_report import build_universe_rows_for_project, load_project_spec, module_complexity_key
from .build_role_section_excerpts import Span, _build_text_and_sidecar, _expand_and_merge, _normalize_path, _read_file


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _exact_role_spans(entry: Dict, code_root: str, file_cache: Dict[str, List[str]]) -> Dict[str, List[Span]]:
    roles = {"ROLE0": [], "ROLE1": [], "ROLE2": []}
    smell_name = str(entry.get("name", ""))
    if smell_name.startswith("Module Cohesion - "):
        abs_path = _normalize_path(entry.get("file_path"), code_root)
        if abs_path and abs_path in file_cache:
            total = len(file_cache[abs_path])
            roles["ROLE0"] = [Span(abs_path, 1, total + 1)]
            for span in entry.get("evidence_lines", []) or []:
                s = int(span["start_line_number"])
                e = int(span["end_line_number"])
                roles["ROLE1"].append(Span(abs_path, max(1, s), max(s + 1, e)))
    elif smell_name.startswith("Module Coupling - "):
        files = entry.get("files", []) or []
        for role, idx in (("ROLE0", 0), ("ROLE1", 1)):
            if idx >= len(files):
                continue
            abs_path = _normalize_path(files[idx].get("name"), code_root)
            if not abs_path or abs_path not in file_cache:
                continue
            for span in files[idx].get("evidence_lines", []) or []:
                s = int(span["start_line_number"])
                e = int(span["end_line_number"])
                roles[role].append(Span(abs_path, max(1, s), max(s + 1, e)))
    return roles


def build_module_complexity_excerpts(
    code_path: str,
    labels_json: str | None,
    report_path: str,
    output_jsonl: str,
    output_sidecar_jsonl: str,
    context_lines: int = 2,
    label_granularity: str = "line",
):
    project_root = Path(code_path).resolve()
    project_name = project_root.name
    project_spec, _ = load_project_spec(project_root, labels_json)

    universe_rows = build_universe_rows_for_project(project_root, project_spec)
    report_rows = _load_json(report_path)
    detected = {module_complexity_key(row): row for row in report_rows}

    file_paths = set()
    for row in universe_rows:
        file_path = row.get("file_path")
        if file_path:
            abs_path = _normalize_path(file_path, str(project_root))
            if abs_path:
                file_paths.add(abs_path)
        for item in row.get("files", []) or []:
            abs_path = _normalize_path(item.get("name"), str(project_root))
            if abs_path:
                file_paths.add(abs_path)
    file_cache = {fp: _read_file(fp).splitlines(keepends=True) for fp in sorted(file_paths) if Path(fp).exists()}

    row_id = 0
    detected_rows = 0
    undetected_rows = 0
    with open(output_jsonl, "w", encoding="utf-8") as out_handle, open(output_sidecar_jsonl, "w", encoding="utf-8") as sidecar_handle:
        for candidate in universe_rows:
            key = module_complexity_key(candidate)
            entry = dict(detected.get(key, candidate))
            is_detected = key in detected
            role_exact = _exact_role_spans(entry, str(project_root), file_cache)
            role_spans = {role: _expand_and_merge(spans, context_lines=context_lines, file_cache=file_cache) for role, spans in role_exact.items()}
            text, tokens, labels, token_map, fallbacks, fallback_used = _build_text_and_sidecar(
                role_spans, role_exact, str(entry.get("name", "")), entry, label_granularity, str(project_root), file_cache
            )
            effective = "line" if (label_granularity == "token" and fallback_used) else label_granularity
            out_row = {
                "id": row_id,
                "smell_name": entry.get("name"),
                "is_detected": is_detected,
                "label_granularity": effective,
                "requested_label_granularity": label_granularity,
                "effective_label_granularity": effective,
                "granularity_fallbacks": fallbacks,
                "text": text,
                "tokens": tokens,
                "labels": labels,
            }
            sidecar_row = {
                "id": row_id,
                "smell_name": entry.get("name"),
                "is_detected": is_detected,
                "label_granularity": effective,
                "requested_label_granularity": label_granularity,
                "effective_label_granularity": effective,
                "granularity_fallbacks": fallbacks,
                "tokenization_backend": "regex-fallback",
                "token_map": token_map,
            }
            out_handle.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            sidecar_handle.write(json.dumps(sidecar_row, ensure_ascii=False) + "\n")
            row_id += 1
            if is_detected:
                detected_rows += 1
            else:
                undetected_rows += 1

    return {"rows": row_id, "detected_rows": detected_rows, "undetected_rows": undetected_rows, "project": project_name, "label_granularity": label_granularity}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build module complexity role-section excerpts.")
    parser.add_argument("code_path", help="Path to a single module-complexity project directory.")
    parser.add_argument("--labels-json", help="Optional labels path. If omitted, uses project-local LABELS/module_complexity_labels.json")
    parser.add_argument("--report", required=True, help="Path to module complexity report JSON")
    parser.add_argument("--output-jsonl", required=True, help="Output JSONL path")
    parser.add_argument("--output-sidecar-jsonl", required=True, help="Output sidecar JSONL path")
    parser.add_argument("--context-lines", type=int, default=2, help="Context lines before/after each span.")
    parser.add_argument("--label-granularity", choices=["line", "token"], default="line", help="Labeling granularity metadata written to outputs.")
    args = parser.parse_args()
    stats = build_module_complexity_excerpts(
        code_path=args.code_path,
        labels_json=args.labels_json,
        report_path=args.report,
        output_jsonl=args.output_jsonl,
        output_sidecar_jsonl=args.output_sidecar_jsonl,
        context_lines=max(0, args.context_lines),
        label_granularity=args.label_granularity,
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
