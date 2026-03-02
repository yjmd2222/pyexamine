from __future__ import annotations

import argparse
import json
import os
import time
from typing import Dict, List

from . import depr_build_role_section_excerpts_jsonl as legacy
from .line_conll_common import build_line_conll_artifacts, write_conll_sample

Span = legacy.Span
Candidate = legacy.Candidate



def build_role_section_excerpts(
    code_path: str,
    report_path: str,
    templates_path: str,
    output_conll: str,
    context_lines: int = 2,
    label_granularity: str = "line",
    progress_every: int = 0,
    slow_row_seconds: float = 0.0,
):
    if label_granularity != "line":
        raise ValueError(
            "The primary generator now supports line granularity only. "
            "Use depr_build_role_section_excerpts_jsonl.py for legacy token/jsonl generation."
        )

    code_root = os.path.abspath(code_path)
    print(f"[stage] start code_root={code_root}", flush=True)
    report_rows = legacy._load_json(report_path)
    print(f"[stage] loaded report rows={len(report_rows)}", flush=True)
    templates = legacy._load_json(templates_path)
    print(f"[stage] loaded templates count={len(templates)}", flush=True)
    smell_template = legacy._template_map(templates)
    print(f"[stage] normalized templates count={len(smell_template)}", flush=True)
    symbols = legacy._parse_symbols(code_root)
    print(
        f"[stage] parsed symbols files={len(symbols['files'])} classes={len(symbols['classes'])} functions={len(symbols['functions'])}",
        flush=True,
    )
    detected_map = legacy._build_detected_candidates(report_rows, code_root)
    detected_keys = set(detected_map.keys())
    print(f"[stage] detected keys={len(detected_keys)}", flush=True)

    file_cache = {fp: legacy._read_file(fp).splitlines(keepends=True) for fp in symbols["files"]}
    print(f"[stage] file cache built files={len(file_cache)}", flush=True)

    candidates: List[Candidate] = []
    for smell_name, template in sorted(smell_template.items()):
        universe_entries = legacy._derive_universe_for_smell(smell_name, template, symbols, code_root)
        seen_keys = set()
        for entry in universe_entries:
            key = legacy._candidate_key(smell_name, entry, code_root)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if key in detected_map:
                row = dict(detected_map[key])
                candidates.append(Candidate(smell_name, key, row, True))
            else:
                candidates.append(Candidate(smell_name, key, entry, False))
        for key, row in detected_map.items():
            if key[0] != smell_name or key in seen_keys:
                continue
            candidates.append(Candidate(smell_name, key, dict(row), True))
    print(f"[stage] candidates built count={len(candidates)}", flush=True)

    detected_rows = 0
    undetected_rows = 0
    row_id = 0
    started_at = time.time()
    with open(output_conll, "w", encoding="utf-8") as out_handle:
        for cand in candidates:
            row_started_at = time.time()
            template = smell_template.get(cand.smell_name)
            if not template:
                continue
            role_spans: Dict[str, List[Span]] = {}
            role_exact_spans: Dict[str, List[Span]] = {}
            role_raw_counts: Dict[str, int] = {}
            role_merged_counts: Dict[str, int] = {}
            role0_expanded: List[Span] = []
            for role in ("ROLE0", "ROLE1", "ROLE2"):
                specs = template.get(role, [])
                raw_spans = legacy._collect_role_spans(cand.entry, specs, code_root)
                raw_spans = [s for s in raw_spans if s.file_path in file_cache]
                exact = list(raw_spans)
                role_exact_spans[role] = exact
                if specs and not raw_spans:
                    raw_spans = legacy._fallback_role_spans(cand.entry, specs, code_root, role0_expanded)
                    raw_spans = [s for s in raw_spans if s.file_path in file_cache]
                    role_raw_counts[role] = len(raw_spans)
                else:
                    role_raw_counts[role] = len(exact)
                merged = legacy._expand_and_merge(raw_spans, context_lines=context_lines, file_cache=file_cache)
                role_spans[role] = merged
                role_merged_counts[role] = len(merged)
                if role == "ROLE0":
                    role0_expanded = merged

            _, conll_rows = build_line_conll_artifacts(
                role_spans=role_spans,
                role_exact_spans=role_exact_spans,
                code_root=code_root,
                file_cache=file_cache,
            )

            out_meta = {
                "id": row_id,
                "smell_name": cand.smell_name,
                "is_detected": cand.is_detected,
                "label_granularity": "line",
                "requested_label_granularity": "line",
                "effective_label_granularity": "line",
                "granularity_fallbacks": [],
            }
            write_conll_sample(out_handle, out_meta, conll_rows)

            row_id += 1
            if cand.is_detected:
                detected_rows += 1
            else:
                undetected_rows += 1

            if progress_every and row_id % progress_every == 0:
                elapsed = time.time() - started_at
                print(
                    f"[progress] rows={row_id} detected={detected_rows} undetected={undetected_rows} elapsed_sec={elapsed:.1f}",
                    flush=True,
                )
            row_elapsed = time.time() - row_started_at
            if slow_row_seconds and row_elapsed >= slow_row_seconds:
                ident = legacy._candidate_identity_info(cand.entry, code_root)
                print(
                    "[slow-row] "
                    f"sec={row_elapsed:.2f} smell={cand.smell_name} "
                    f"file={ident.get('file_path')} class={ident.get('class_name')} "
                    f"method_or_function={ident.get('method_or_function')} "
                    f"start={ident.get('start_line_number')} end={ident.get('end_line_number')} "
                    f"role_raw_counts={role_raw_counts} role_merged_counts={role_merged_counts} "
                    f"tokens={len(conll_rows)}",
                    flush=True,
                )

    return {
        "rows": row_id,
        "detected_rows": detected_rows,
        "undetected_rows": undetected_rows,
        "detected_keys": len(detected_keys),
        "label_granularity": "line",
        "output_format": "conll",
    }



def main():
    parser = argparse.ArgumentParser(
        description="Build line-level role-section excerpts as canonical CoNLL."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--report", required=True, help="Path to code_quality_report.json")
    parser.add_argument(
        "--templates",
        default="master-thesis-materials/data/templates_with_roles.json",
        help="Path to templates_with_roles.json",
    )
    parser.add_argument(
        "--output-conll",
        default=None,
        help="Path to output CoNLL file.",
    )
    parser.add_argument(
        "--output-jsonl",
        default=None,
        help="Deprecated alias for output CoNLL path. If provided, the file written is still CoNLL.",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=2,
        help="Context lines to include before/after each span.",
    )
    parser.add_argument(
        "--label-granularity",
        choices=["line"],
        default="line",
        help="Only line granularity is supported by the primary CoNLL generator.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=0,
        help="Print periodic progress every N rows (0 disables progress logs).",
    )
    parser.add_argument(
        "--slow-row-seconds",
        type=float,
        default=0.0,
        help="Warn if one row takes longer than this many seconds (0 disables warnings).",
    )
    args = parser.parse_args()

    output_conll = args.output_conll or args.output_jsonl or "role_section_excerpts.line.conll"

    stats = build_role_section_excerpts(
        code_path=args.code_path,
        report_path=args.report,
        templates_path=args.templates,
        output_conll=output_conll,
        context_lines=max(0, args.context_lines),
        label_granularity=args.label_granularity,
        progress_every=max(0, args.progress_every),
        slow_row_seconds=max(0.0, args.slow_row_seconds),
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
