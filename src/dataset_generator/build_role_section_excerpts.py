import argparse
import bisect
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


ROLES = ("ROLE0", "ROLE1", "ROLE2")
ROLE_LABEL = {"ROLE0": "ROLE0-E", "ROLE1": "ROLE1-E", "ROLE2": "ROLE2-E"}


@dataclass
class RoleCodeSpan:
    role: str
    file_path: str
    start_line: int
    end_line: int
    start_char: int
    end_char: int
    render_start: int
    render_end: int
    text: str
    local_line_starts: List[int]


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _to_abs(code_root: str, rel: Optional[str]) -> Optional[str]:
    if not rel:
        return None
    normalized = rel.replace("\\", "/")
    if os.path.isabs(normalized):
        return normalized
    candidate = os.path.abspath(os.path.join(code_root, normalized))
    if os.path.exists(candidate):
        return candidate
    root_name = os.path.basename(os.path.normpath(code_root)).replace("\\", "/")
    prefix = root_name + "/"
    if normalized.startswith(prefix):
        candidate2 = os.path.abspath(os.path.join(code_root, normalized[len(prefix) :]))
        if os.path.exists(candidate2):
            return candidate2
    return candidate


def _slice_file_lines(file_path: str, start_line: int, end_line: int, cache: Dict[str, List[str]]) -> str:
    if file_path not in cache:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            cache[file_path] = f.readlines()
    lines = cache[file_path]
    s = max(1, int(start_line))
    e = max(s, int(end_line))
    return "".join(lines[s - 1 : e - 1])


def _line_starts(text: str) -> List[int]:
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _collect_role_mentions(evidence: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    by_role: Dict[str, List[Dict[str, Any]]] = {r: [] for r in ROLES}
    seen: Dict[str, set] = {r: set() for r in ROLES}
    for m in evidence.get("mentions", []):
        source_roles = m.get("source_roles")
        if not isinstance(source_roles, list):
            role = m.get("role")
            source_roles = [role] if role in ROLES else []
        for role in source_roles:
            if role not in ROLES:
                continue
            key = (
                m.get("file"),
                int(m.get("start_line", 0) or 0),
                int(m.get("end_line", 0) or 0),
                int(m.get("start_char", 0) or 0),
                int(m.get("end_char", 0) or 0),
            )
            if key in seen[role]:
                continue
            seen[role].add(key)
            by_role[role].append(m)
    for role in ROLES:
        by_role[role].sort(
            key=lambda m: (
                str(m.get("file", "")),
                int(m.get("start_line", 0) or 0),
                int(m.get("start_char", 0) or 0),
            )
        )
    return by_role


def _tokenize(text: str, tokenizer_name: str) -> Tuple[List[str], List[Tuple[int, int]], str]:
    try:
        from transformers import AutoTokenizer  # type: ignore

        tok = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
        enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
        tokens = tok.convert_ids_to_tokens(enc["input_ids"])
        offsets = [tuple(x) for x in enc["offset_mapping"]]
        return tokens, offsets, f"hf:{tokenizer_name}"
    except Exception:
        matches = list(re.finditer(r"\S+", text))
        tokens = [m.group(0) for m in matches]
        offsets = [(m.start(), m.end()) for m in matches]
        return tokens, offsets, "regex-fallback"


def _find_span_for_offset(spans: List[RoleCodeSpan], start: int, end: int) -> Optional[RoleCodeSpan]:
    for sp in spans:
        if start >= sp.render_start and end <= sp.render_end:
            return sp
    return None


def _map_to_source(span: RoleCodeSpan, token_start: int, token_end: int) -> Tuple[int, int, int, int]:
    local_s = max(0, token_start - span.render_start)
    local_e = max(local_s, token_end - span.render_start)
    ls = span.local_line_starts
    line_idx_s = bisect.bisect_right(ls, local_s) - 1
    line_idx_e = bisect.bisect_right(ls, local_e) - 1
    line_idx_s = max(0, line_idx_s)
    line_idx_e = max(0, line_idx_e)
    source_line_s = span.start_line + line_idx_s
    source_line_e = span.start_line + line_idx_e
    source_col_s = local_s - ls[line_idx_s]
    source_col_e = local_e - ls[line_idx_e]
    return source_line_s, source_col_s, source_line_e, source_col_e


def build_role_section_excerpts(
    detr_path: str,
    output_jsonl: str,
    output_sidecar_jsonl: str,
    tokenizer_name: str = "answerdotai/ModernBERT-large",
) -> Dict[str, Any]:
    detr = _load_json(detr_path)
    code_root = detr.get("code_root") or os.getcwd()
    evidences = detr.get("Evidences", [])
    file_cache: Dict[str, List[str]] = {}

    os.makedirs(os.path.dirname(os.path.abspath(output_jsonl)) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_sidecar_jsonl)) or ".", exist_ok=True)

    num_written = 0
    num_dropped_empty = 0
    tokenization_backend = None

    with open(output_jsonl, "w", encoding="utf-8") as out_f, open(
        output_sidecar_jsonl, "w", encoding="utf-8"
    ) as sidecar_f:
        for ev in evidences:
            role_mentions = _collect_role_mentions(ev)
            rendered_parts: List[str] = []
            structural_spans: List[Tuple[int, int]] = []
            role_code_spans: List[RoleCodeSpan] = []
            cursor = 0

            def add_part(text: str, structural: bool = False) -> Tuple[int, int]:
                nonlocal cursor
                start = cursor
                rendered_parts.append(text)
                cursor += len(text)
                end = cursor
                if structural and end > start:
                    structural_spans.append((start, end))
                return start, end

            for role in ROLES:
                add_part(f"[{role}]\n", structural=True)
                for m in role_mentions[role]:
                    rel_path = m.get("file")
                    abs_path = _to_abs(code_root, rel_path)
                    if not abs_path:
                        continue
                    start_line = int(m.get("start_line", 1) or 1)
                    end_line = int(m.get("end_line", start_line + 1) or (start_line + 1))
                    try:
                        excerpt_text = _slice_file_lines(abs_path, start_line, end_line, file_cache)
                    except OSError:
                        continue
                    add_part("[FILE]\n", structural=True)
                    add_part(f"path={rel_path}\n", structural=True)
                    rs, re_ = add_part(excerpt_text, structural=False)
                    add_part("[SEP_EXCERPT]\n", structural=True)
                    role_code_spans.append(
                        RoleCodeSpan(
                            role=role,
                            file_path=rel_path or "",
                            start_line=start_line,
                            end_line=end_line,
                            start_char=int(m.get("start_char", 0) or 0),
                            end_char=int(m.get("end_char", 0) or 0),
                            render_start=rs,
                            render_end=re_,
                            text=excerpt_text,
                            local_line_starts=_line_starts(excerpt_text),
                        )
                    )
                add_part("\n", structural=True)

            if not role_code_spans:
                num_dropped_empty += 1
                continue

            text = "".join(rendered_parts)
            tokens, offsets, backend = _tokenize(text, tokenizer_name)
            if tokenization_backend is None:
                tokenization_backend = backend

            labels: List[Any] = []
            token_map: List[Dict[str, Any]] = []

            for idx, (tok, (ts, te)) in enumerate(zip(tokens, offsets)):
                if te <= ts:
                    labels.append(-100)
                    token_map.append({"token_idx": idx, "token": tok, "start": ts, "end": te, "is_structural": True})
                    continue

                is_structural = any(ts >= s and te <= e for s, e in structural_spans)
                if is_structural:
                    label = -100
                    token_map.append({"token_idx": idx, "token": tok, "start": ts, "end": te, "is_structural": True})
                    labels.append(label)
                    continue

                matched = _find_span_for_offset(role_code_spans, ts, te)
                if matched is None:
                    label = 0
                    token_map.append({"token_idx": idx, "token": tok, "start": ts, "end": te, "is_structural": False})
                    labels.append(label)
                    continue

                label = ROLE_LABEL[matched.role]
                src_ls, src_cs, src_le, src_ce = _map_to_source(matched, ts, te)
                labels.append(label)
                token_map.append(
                    {
                        "token_idx": idx,
                        "token": tok,
                        "start": ts,
                        "end": te,
                        "is_structural": False,
                        "role": matched.role,
                        "label": label,
                        "file_path": matched.file_path,
                        "source_line_start": src_ls,
                        "source_col_start": src_cs,
                        "source_line_end": src_le,
                        "source_col_end": src_ce,
                        "source_span_start_line": matched.start_line,
                        "source_span_end_line": matched.end_line,
                        "source_span_start_char": matched.start_char,
                        "source_span_end_char": matched.end_char,
                    }
                )

            record = {
                "id": ev.get("id"),
                "smell_name": ev.get("smell_name"),
                "is_detected": ev.get("is_detected"),
                "text": text,
                "tokens": tokens,
                "labels": labels,
            }
            sidecar = {
                "id": ev.get("id"),
                "smell_name": ev.get("smell_name"),
                "tokenization_backend": backend,
                "token_map": token_map,
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            sidecar_f.write(json.dumps(sidecar, ensure_ascii=False) + "\n")
            num_written += 1

    return {
        "num_instances": num_written,
        "dropped_without_role_spans": num_dropped_empty,
        "tokenization_backend": tokenization_backend,
        "output_jsonl": os.path.abspath(output_jsonl),
        "output_sidecar_jsonl": os.path.abspath(output_sidecar_jsonl),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build role-section token-classification training artifacts from DETR candidates."
    )
    parser.add_argument("--detr", required=True, help="Path to detr_candidates.json (or compatible DETR JSON)")
    parser.add_argument("--output-jsonl", default="role_section_excerpts.jsonl", help="Output training JSONL path")
    parser.add_argument(
        "--output-sidecar-jsonl",
        default="role_section_excerpts.sidecar.jsonl",
        help="Output per-token sidecar JSONL path",
    )
    parser.add_argument(
        "--tokenizer",
        default="answerdotai/ModernBERT-large",
        help="Tokenizer name for per-token labels/sidecar mapping",
    )
    args = parser.parse_args()

    summary = build_role_section_excerpts(
        detr_path=args.detr,
        output_jsonl=args.output_jsonl,
        output_sidecar_jsonl=args.output_sidecar_jsonl,
        tokenizer_name=args.tokenizer,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
