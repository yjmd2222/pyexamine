import argparse
import io
import json
import os
import tokenize


LABEL_PRIORITY = {
    "callfrom": 3,
    "within": 2,
    "primary": 1,
}


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_code_files(root_path):
    if os.path.isfile(root_path):
        if root_path.endswith(".py"):
            yield os.path.abspath(root_path)
        return
    for root, _, files in os.walk(root_path):
        for filename in files:
            if filename.endswith(".py"):
                yield os.path.abspath(os.path.join(root, filename))


def _tokenize_by_line(content):
    token_lines = {}
    reader = io.StringIO(content)
    try:
        tokens = tokenize.generate_tokens(reader.readline)
    except tokenize.TokenError:
        return token_lines

    for token_type, token_str, start, _, _ in tokens:
        if token_type in (tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        if token_type in (tokenize.NL, tokenize.NEWLINE):
            continue
        row = start[0]
        if not token_str:
            continue
        token_lines.setdefault(row, []).append(token_str)
    return token_lines


def _read_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _normalize_path(path, code_root):
    if not path:
        return None
    if os.path.isabs(path) and os.path.exists(path):
        return path
    if os.path.exists(path):
        return os.path.abspath(path)
    if path.endswith(".py"):
        candidate = os.path.abspath(os.path.join(code_root, path))
        if os.path.exists(candidate):
            return candidate
    module_candidate = path.replace(".", os.path.sep)
    candidate = os.path.abspath(os.path.join(code_root, f"{module_candidate}.py"))
    if os.path.exists(candidate):
        return candidate
    return None


def _get_value(entry, *keys):
    for key in keys:
        if key in entry:
            return entry[key]
    return None


def _normalize_name(name):
    if not name:
        return None
    return " ".join(name.strip().split()).lower()


def _extract_spans(entry, scheme, code_root):
    spans = []
    file_path = _get_value(entry, "file_path", "File")
    if file_path:
        file_path = _normalize_path(file_path, code_root)

    has_within = "I-WITHIN" in scheme
    has_callfrom = "B-CALLFROM" in scheme

    start_line = _get_value(entry, "start_line_number", "Start Line Number")
    end_line = _get_value(entry, "end_line_number", "End Line Number")
    if file_path and start_line and end_line:
        spans.append((file_path, start_line, end_line, "primary"))

    instance_lines = _get_value(entry, "instance_lines", "Instance Lines") or []
    if file_path and instance_lines:
        label_type = "within" if has_within and start_line and end_line else "primary"
        for span in instance_lines:
            span_start = _get_value(span, "start_line_number", "Start Line Number")
            span_end = _get_value(span, "end_line_number", "End Line Number")
            if span_start and span_end:
                spans.append((file_path, span_start, span_end, label_type))

    line_spans = _get_value(entry, "lines", "Lines") or []
    if file_path and line_spans:
        for span in line_spans:
            span_start = _get_value(span, "start_line_number", "Start Line Number")
            span_end = _get_value(span, "end_line_number", "End Line Number")
            if span_start and span_end:
                spans.append((file_path, span_start, span_end, "primary"))

    class_spans = _get_value(entry, "classes", "Classes") or []
    if file_path and class_spans:
        for span in class_spans:
            span_start = _get_value(span, "start_line_number", "Start Line Number")
            span_end = _get_value(span, "end_line_number", "End Line Number")
            if span_start and span_end:
                spans.append((file_path, span_start, span_end, "primary"))

    method_spans = _get_value(entry, "methods_functions", "Methods Functions") or []
    if file_path and method_spans:
        for span in method_spans:
            span_start = _get_value(span, "start_line_number", "Start Line Number")
            span_end = _get_value(span, "end_line_number", "End Line Number")
            if span_start and span_end:
                spans.append((file_path, span_start, span_end, "primary"))

    outgoing_lines = _get_value(entry, "outgoing_instance_lines", "Outgoing Instance Lines") or []
    if file_path and outgoing_lines:
        for span in outgoing_lines:
            span_start = _get_value(span, "start_line_number", "Start Line Number")
            span_end = _get_value(span, "end_line_number", "End Line Number")
            if span_start and span_end:
                spans.append((file_path, span_start, span_end, "primary"))

    files = _get_value(entry, "files", "Files") or []
    for file_entry in files:
        other_path = _get_value(file_entry, "name", "Name")
        if not other_path:
            continue
        other_path = _normalize_path(other_path, code_root)
        if not other_path:
            continue
        incoming_lines = _get_value(file_entry, "incoming_instance_lines", "Incoming Instance Lines")
        instance_lines = _get_value(file_entry, "instance_lines", "Instance Lines")
        if incoming_lines:
            label_type = "callfrom" if has_callfrom else "primary"
            for span in incoming_lines:
                span_start = _get_value(span, "start_line_number", "Start Line Number")
                span_end = _get_value(span, "end_line_number", "End Line Number")
                if span_start and span_end:
                    spans.append((other_path, span_start, span_end, label_type))
        elif instance_lines:
            label_type = "callfrom" if has_callfrom else "primary"
            for span in instance_lines:
                span_start = _get_value(span, "start_line_number", "Start Line Number")
                span_end = _get_value(span, "end_line_number", "End Line Number")
                if span_start and span_end:
                    spans.append((other_path, span_start, span_end, label_type))

    return spans


def _build_smell_spans(report_entries, smell_schemes, name_to_slug, code_root):
    spans_by_smell = {}
    normalized_name_to_slug = {
        _normalize_name(name): slug
        for name, slug in name_to_slug.items()
    }
    for entry in report_entries:
        name = _get_value(entry, "name", "Name")
        if not name:
            continue
        slug = name_to_slug.get(name)
        if not slug:
            slug = normalized_name_to_slug.get(_normalize_name(name))
        if not slug:
            continue
        scheme = smell_schemes.get(slug, "A")
        spans = _extract_spans(entry, scheme_labels[scheme], code_root)
        if not spans:
            continue
        spans_by_smell.setdefault(slug, []).extend(spans)
    return spans_by_smell


def _label_for_token(line_number, spans, scheme_labels):
    matching = []
    for start, end, label_type in spans:
        if start <= line_number < end:
            matching.append((label_type, start, end))
    if not matching:
        return "O"
    matching.sort(key=lambda item: (-LABEL_PRIORITY[item[0]], item[1], item[2]))
    label_type, start, _ = matching[0]
    if label_type == "callfrom":
        return "B-CALLFROM" if line_number == start else "I-CALLFROM"
    if label_type == "within":
        return "I-WITHIN"
    return "B" if line_number == start else "I"


def _write_conll(handle, file_path, content, spans, scheme_labels):
    handle.write("[file]\t-100\n")
    handle.write(f"path={file_path}\t-100\n\n")

    token_lines = _tokenize_by_line(content)
    for row in sorted(token_lines):
        label = _label_for_token(row, spans, scheme_labels)
        if label not in scheme_labels:
            label = "O"
        for token_str in token_lines[row]:
            handle.write(f"{token_str}\t{label}\n")
        handle.write("\n")


def build_dataset(code_root, report_path, labels_path, output_dir):
    report_entries = _load_json(report_path)
    labels_data = _load_json(labels_path)
    smell_schemes = labels_data["smell_schemes"]
    name_to_slug = labels_data["slug_map"]
    global scheme_labels
    scheme_labels = labels_data["schemes"]

    code_root = os.path.abspath(code_root)
    spans_by_smell = _build_smell_spans(report_entries, smell_schemes, name_to_slug, code_root)

    os.makedirs(output_dir, exist_ok=True)
    for slug, spans in spans_by_smell.items():
        spans_by_file = {}
        for file_path, start, end, label_type in spans:
            spans_by_file.setdefault(file_path, []).append((start, end, label_type))
        output_path = os.path.join(output_dir, f"{slug}.conll")
        with open(output_path, "w", encoding="utf-8") as handle:
            for file_path, file_spans in sorted(spans_by_file.items()):
                content = _read_file(file_path)
                scheme = smell_schemes.get(slug, "A")
                _write_conll(handle, file_path, content, file_spans, scheme_labels[scheme])


def main():
    parser = argparse.ArgumentParser(description="Build per-smell CoNLL datasets from source code and a PyExamine report.")
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--report", required=True, help="Path to code_quality_report.json")
    parser.add_argument("--labels", default="master-thesis-materials/data/labels.json",
                        help="Path to labels.json")
    parser.add_argument("--output-dir", default="dataset_conll", help="Output directory")
    args = parser.parse_args()

    build_dataset(args.code_path, args.report, args.labels, args.output_dir)


if __name__ == "__main__":
    main()
