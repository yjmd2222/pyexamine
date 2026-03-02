from __future__ import annotations

import io
import json
import tokenize
from typing import Dict, Iterable, List, Optional, Tuple

from .depr_build_role_section_excerpts_jsonl import (
    Span,
    _display_path,
    _line_in_ranges,
    _normalize_path,
    _render_role_section,
)

ROLES = ("ROLE0", "ROLE1", "ROLE2")


def _escape_conll_token(token: str) -> str:
    return token.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')


def _indent_token(indent_text: str) -> str:
    if not indent_text:
        return "[INDENT]"
    visible = indent_text.replace(' ', '·').replace('\t', '\\t')
    return f"[INDENT:{visible}]"


def _build_exact_index(role_exact_spans: Dict[str, List[Span]], code_root: str) -> Dict[str, Dict[str, List[Tuple[int, int, int]]]]:
    exact_index: Dict[str, Dict[str, List[Tuple[int, int, int]]]] = {}
    for role in ROLES:
        by_file: Dict[str, List[Tuple[int, int, int]]] = {}
        for entry_id, span in enumerate(role_exact_spans.get(role, [])):
            display = _display_path(span.file_path, code_root)
            by_file.setdefault(display, []).append((span.start_line, span.end_line, entry_id))
        exact_index[role] = by_file
    return exact_index


def _build_packed_text_and_blocks(
    role_spans: Dict[str, List[Span]],
    role_exact_spans: Dict[str, List[Span]],
    code_root: str,
    file_cache: Dict[str, List[str]],
) -> Tuple[str, List[Dict], Dict[str, Dict[str, List[Tuple[int, int, int]]]]]:
    text_parts: List[str] = []
    segments: List[Dict] = []
    for role in ROLES:
        spans = role_spans.get(role, [])
        section_text, section_meta = _render_role_section(role, spans, code_root, file_cache)
        text_parts.append(section_text)
        segments.extend(section_meta)

    text = "".join(text_parts)
    exact_index = _build_exact_index(role_exact_spans, code_root)

    code_blocks: List[Dict] = []
    role: Optional[str] = None
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
            segment = None
            for seg in segments:
                if seg["role"] == role and seg["file_path"] == path and not seg.get("_used"):
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

    return text, code_blocks, exact_index


def _line_offsets(text: str) -> List[int]:
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _absolute_char(offsets: List[int], row: int, col: int) -> int:
    if row <= 0:
        return 0
    if row > len(offsets):
        return offsets[-1]
    return offsets[row - 1] + col


def _token_label(role: str, line_no: Optional[int], exact_ranges: List[Tuple[int, int, int]], prev_positive: Dict) -> Tuple[object, Dict]:
    if line_no is None:
        return -100, {"role": None, "file_path": None, "range": None, "line_no": None}
    line_range = _line_in_ranges(line_no, exact_ranges)
    if line_range is None:
        return "O", {"role": None, "file_path": None, "range": None, "line_no": None}
    if (
        prev_positive.get("role") == role
        and prev_positive.get("range") == line_range
        and prev_positive.get("line_no") == line_no
    ):
        label = f"I-{role}"
    else:
        label = f"B-{role}"
    return label, {"role": role, "file_path": None, "range": line_range, "line_no": line_no}


def _emit_structural_token(
    conll_rows: List[Dict],
    token: str,
    _start: Optional[int],
    _end: Optional[int],
    _role: Optional[str],
) -> None:
    conll_rows.append({"token": token, "label": -100})


def _emit_code_tokens(
    block: Dict,
    conll_rows: List[Dict],
    prev_positive: Dict,
) -> Dict:
    text = block["excerpt_text"]
    offsets = _line_offsets(text)
    reader = io.StringIO(text)
    try:
        stream = list(tokenize.generate_tokens(reader.readline))
    except (tokenize.TokenError, IndentationError):
        stream = []
        line_starts = _line_offsets(text)
        for row_idx, line in enumerate(text.splitlines(keepends=True), start=1):
            if not line:
                continue
            line_no = block["source_line_start"] + row_idx - 1
            line_start = line_starts[row_idx - 1]
            indent_len = len(line) - len(line.lstrip(" \t"))
            stripped = line[indent_len:]
            body_start = line_start + indent_len
            if stripped.rstrip("\r\n"):
                token_text = stripped.rstrip("\r\n")
                start = block["text_start"] + body_start
                end = start + len(token_text)
                label, prev_positive = _token_label(block["role"], line_no, block.get("exact_ranges", []), prev_positive)
                conll_rows.append({"token": token_text, "label": label})
        return prev_positive

    for tok in stream:
        tok_type = tok.type
        if tok_type in (tokenize.ENDMARKER, tokenize.ENCODING):
            continue
        raw = tok.string
        token_text: Optional[str] = None
        source_line: Optional[int] = None
        source_line_end: Optional[int] = None
        source_col_start: Optional[int] = None
        source_col_end: Optional[int] = None
        start_abs: Optional[int] = None
        end_abs: Optional[int] = None
        label: object = -100

        if tok_type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT):
            continue
        if tok_type == tokenize.DEDENT:
            prev_positive = {"role": None, "file_path": None, "range": None, "line_no": None}
            continue
        if not raw:
            continue
        token_text = raw

        srow, scol = tok.start
        erow, ecol = tok.end
        start_abs = block["text_start"] + _absolute_char(offsets, srow, scol)
        end_abs = block["text_start"] + _absolute_char(offsets, erow, ecol)
        source_line = block["source_line_start"] + srow - 1
        source_line_end = block["source_line_start"] + erow - 1
        source_col_start = scol
        source_col_end = ecol

        label, prev_positive = _token_label(block["role"], source_line, block.get("exact_ranges", []), prev_positive)

        conll_rows.append({"token": token_text, "label": label})
    return prev_positive


def _format_path_marker(path_marker: str, block: Optional[Dict]) -> str:
    if block is None or not path_marker.startswith("path="):
        return path_marker
    start_line = block["source_line_start"]
    end_line = max(start_line, block["source_span_end_line"] - 1)
    return f"{path_marker}#L{start_line}-L{end_line}"


def build_line_conll_artifacts(
    role_spans: Dict[str, List[Span]],
    role_exact_spans: Dict[str, List[Span]],
    code_root: str,
    file_cache: Dict[str, List[str]],
) -> Tuple[str, List[Dict]]:
    packed_text, code_blocks, _ = _build_packed_text_and_blocks(role_spans, role_exact_spans, code_root, file_cache)
    block_by_text_start = {block["text_start"]: block for block in code_blocks}
    conll_rows: List[Dict] = []
    prev_positive = {"role": None, "file_path": None, "range": None}
    i = 0
    current_role: Optional[str] = None
    while i < len(packed_text):
        if packed_text.startswith("[ROLE0]\n", i):
            _emit_structural_token(conll_rows, "[ROLE0]", i, i + len("[ROLE0]"), "ROLE0")
            current_role = "ROLE0"
            prev_positive = {"role": None, "file_path": None, "range": None}
            i += len("[ROLE0]\n")
            continue
        if packed_text.startswith("[ROLE1]\n", i):
            _emit_structural_token(conll_rows, "[ROLE1]", i, i + len("[ROLE1]"), "ROLE1")
            current_role = "ROLE1"
            prev_positive = {"role": None, "file_path": None, "range": None}
            i += len("[ROLE1]\n")
            continue
        if packed_text.startswith("[ROLE2]\n", i):
            _emit_structural_token(conll_rows, "[ROLE2]", i, i + len("[ROLE2]"), "ROLE2")
            current_role = "ROLE2"
            prev_positive = {"role": None, "file_path": None, "range": None}
            i += len("[ROLE2]\n")
            continue
        if packed_text.startswith("[FILE]\n", i):
            _emit_structural_token(conll_rows, "[FILE]", i, i + len("[FILE]"), current_role)
            prev_positive = {"role": None, "file_path": None, "range": None}
            i += len("[FILE]\n")
            if packed_text.startswith("path=", i):
                path_end = packed_text.find("\n", i)
                if path_end < 0:
                    path_end = len(packed_text)
                code_start = path_end + 1
                block = block_by_text_start.get(code_start)
                path_token = _format_path_marker(packed_text[i:path_end], block)
                _emit_structural_token(conll_rows, path_token, i, path_end, current_role)
                i = code_start
            block = block_by_text_start.get(i)
            if block is not None:
                prev_positive = _emit_code_tokens(block, conll_rows, prev_positive)
                i = block["text_end"]
            if packed_text.startswith("\n[SEP_EXCERPT]\n", i):
                sep_start = i + 1
                _emit_structural_token(conll_rows, "[SEP_EXCERPT]", sep_start, sep_start + len("[SEP_EXCERPT]"), current_role)
                prev_positive = {"role": None, "file_path": None, "range": None}
                i += len("\n[SEP_EXCERPT]\n")
            continue
        if packed_text[i] == '\n':
            i += 1
            continue
        # Defensive fallback: skip unexpected characters between deterministic markers.
        i += 1
    return packed_text, conll_rows


def write_conll_sample(handle, metadata: Dict, conll_rows: List[Dict]) -> None:
    header_keys = [
        "id",
        "smell_name",
        "is_detected",
        "label_granularity",
        "requested_label_granularity",
        "effective_label_granularity",
    ]
    for key in header_keys:
        if key in metadata:
            handle.write(f"# {key} = {json.dumps(metadata[key], ensure_ascii=False)}\n")
    if metadata.get("granularity_fallbacks") is not None:
        handle.write(
            "# granularity_fallbacks = "
            + json.dumps(metadata.get("granularity_fallbacks", []), ensure_ascii=False)
            + "\n"
        )
    for row in conll_rows:
        token = _escape_conll_token(str(row["token"]))
        label = row["label"]
        handle.write(f"{token}\t{label}\n")
    handle.write("\n")
