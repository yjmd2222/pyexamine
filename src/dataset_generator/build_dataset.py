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

LABELS = {
    "schemes": {
        "A": ["O", "B", "I"],
        "B": ["O", "B", "I", "I-WITHIN"],
        "C": ["O", "B", "I", "B-CALLFROM", "I-CALLFROM"],
        "D": ["O", "B", "I", "I-WITHIN", "B-CALLFROM", "I-CALLFROM"],
    },
    "labels_by_scheme": {
        "A": {
            "labels": ["O", "B", "I"],
            "id2label": {"0": "O", "1": "B", "2": "I"},
            "label2id": {"O": 0, "B": 1, "I": 2},
        },
        "B": {
            "labels": ["O", "B", "I", "I-WITHIN"],
            "id2label": {"0": "O", "1": "B", "2": "I", "3": "I-WITHIN"},
            "label2id": {"O": 0, "B": 1, "I": 2, "I-WITHIN": 3},
        },
        "C": {
            "labels": ["O", "B", "I", "B-CALLFROM", "I-CALLFROM"],
            "id2label": {"0": "O", "1": "B", "2": "I", "3": "B-CALLFROM", "4": "I-CALLFROM"},
            "label2id": {"O": 0, "B": 1, "I": 2, "B-CALLFROM": 3, "I-CALLFROM": 4},
        },
        "D": {
            "labels": ["O", "B", "I", "I-WITHIN", "B-CALLFROM", "I-CALLFROM"],
            "id2label": {
                "0": "O",
                "1": "B",
                "2": "I",
                "3": "I-WITHIN",
                "4": "B-CALLFROM",
                "5": "I-CALLFROM",
            },
            "label2id": {"O": 0, "B": 1, "I": 2, "I-WITHIN": 3, "B-CALLFROM": 4, "I-CALLFROM": 5},
        },
    },
    "slug_map": {
        "Long Method": "long-method",
        "Large Class": "large-class-1",
        "Primitive Obsession": "primitive-obsession",
        "Long Parameter List": "long-parameter-list",
        "Data Clumps": "data-clumps",
        "Switch Statements": "switch-statements",
        "Temporary Field": "temporary-field",
        "Alternative Classes with Different Interfaces": "alternative-classes-with-different-interfaces",
        "Potential Divergent Change": "potential-divergent-change",
        "Parallel Inheritance Hierarchies": "parallel-inheritance-hierarchies",
        "Potential Shotgun Surgery": "potential-shotgun-surgery",
        "Excessive Comments": "excessive-comments",
        "Duplicate Code": "duplicate-code",
        "Data Class": "data-class",
        "Dead Code": "dead-code",
        "Lazy Class": "lazy-class",
        "Speculative Generality": "speculative-generality",
        "Feature Envy": "feature-envy",
        "Inappropriate Intimacy": "inappropriate-intimacy",
        "Message Chains": "message-chains",
        "Middle Man": "middle-man",
        "Hub-like Dependency": "hub-like-dependency",
        "Scattered Functionality": "scattered-functionality",
        "Potential Redundant Abstractions": "potential-redundant-abstractions",
        "God Object": "god-object",
        "Potential Improper API Usage": "potential-improper-api-usage",
        "Orphan Module": "orphan-module",
        "Cyclic Dependency": "cyclic-dependency",
        "Unstable Dependency": "unstable-dependency",
        "High Number of Methods (NOM)": "high-number-of-methods",
        "High Weighted Methods per Class (WMPC)": "high-weighted-methods-per-class",
        "Large Class (SIZE2)": "large-class-2",
        "High Weight of a Class (WAC)": "high-weight-of-a-class",
        "High Lack of Cohesion of Methods (LCOM)": "high-lack-of-cohesion-of-methods",
        "High Response for a Class (RFC)": "high-response-for-a-class",
        "High Number of Classes per Module": "high-number-of-classes-per-module",
        "Deep Inheritance Tree (DIT)": "deep-inheritance-tree",
        "High Lines of Code (LOC)": "high-lines-of-code",
        "High Message Passing Coupling (MPC)": "high-message-passing-coupling",
        "High Coupling Between Object Classes (CBO)": "high-coupling-between-object-classes",
        "High Number of classes Per Project": "high-number-of-classes-per-project",
        "High Cyclomatic Complexity": "high-cyclomatic-complexity",
        "High Fan-out": "high-fan-out",
        "High Fan-in": "high-fan-in",
        "Long File": "long-file",
        "Too Many Branches": "too-many-branches",
    },
    "smell_schemes": {
        "long-method": "A",
        "large-class-1": "A",
        "primitive-obsession": "A",
        "long-parameter-list": "A",
        "data-clumps": "A",
        "switch-statements": "A",
        "temporary-field": "A",
        "alternative-classes-with-different-interfaces": "A",
        "potential-divergent-change": "B",
        "parallel-inheritance-hierarchies": "A",
        "potential-shotgun-surgery": "A",
        "excessive-comments": "A",
        "duplicate-code": "A",
        "data-class": "B",
        "dead-code": "A",
        "lazy-class": "A",
        "speculative-generality": "B",
        "feature-envy": "B",
        "inappropriate-intimacy": "B",
        "message-chains": "A",
        "middle-man": "B",
        "hub-like-dependency": "D",
        "scattered-functionality": "C",
        "potential-redundant-abstractions": "A",
        "god-object": "B",
        "potential-improper-api-usage": "A",
        "orphan-module": "A",
        "cyclic-dependency": "A",
        "unstable-dependency": "D",
        "high-number-of-methods": "A",
        "high-weighted-methods-per-class": "A",
        "large-class-2": "A",
        "high-weight-of-a-class": "A",
        "high-lack-of-cohesion-of-methods": "A",
        "high-response-for-a-class": "A",
        "high-number-of-classes-per-module": "A",
        "deep-inheritance-tree": "A",
        "high-lines-of-code": "A",
        "high-message-passing-coupling": "B",
        "high-coupling-between-object-classes": "B",
        "high-number-of-classes-per-project": "A",
        "high-cyclomatic-complexity": "A",
        "high-fan-out": "A",
        "high-fan-in": "C",
        "long-file": "A",
        "too-many-branches": "A",
    },
    "unmapped_smells": [],
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
    def _normalize_indentation(text):
        normalized_lines = []
        for line in text.splitlines(keepends=True):
            stripped = line.lstrip(" \t")
            if stripped == line:
                normalized_lines.append(line)
                continue
            leading = line[: len(line) - len(stripped)]
            expanded = leading.expandtabs(4)
            count = len(expanded)
            if count % 4 != 0:
                count = ((count + 3) // 4) * 4
            normalized_lines.append((" " * count) + stripped)
        return "".join(normalized_lines)

    content = _normalize_indentation(content)
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


def _default_output_dir(code_path):
    candidate = os.path.abspath(code_path)
    if os.path.isfile(candidate) or candidate.endswith(".py"):
        candidate = os.path.dirname(candidate)
    base_name = os.path.basename(os.path.normpath(candidate))
    base_name = base_name or "code"
    return f"dataset_{base_name}"


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


def _write_conll(handle, display_path, content, spans, scheme_labels, label_full_file=False):
    handle.write("[file]\t-100\n")
    handle.write(f"path={display_path}\t-100\n\n")

    token_lines = _tokenize_by_line(content)
    first_row = min(token_lines) if token_lines else None
    for row in sorted(token_lines):
        if label_full_file:
            label = "B" if row == first_row else "I"
        else:
            label = _label_for_token(row, spans, scheme_labels)
        if label not in scheme_labels:
            label = "O"
        tokens = token_lines[row]
        if label.startswith("B") and len(tokens) > 1:
            if label == "B-CALLFROM":
                continuation = "I-CALLFROM"
            else:
                continuation = "I"
            handle.write(f"{tokens[0]}\t{label}\n")
            for token_str in tokens[1:]:
                handle.write(f"{token_str}\t{continuation}\n")
        else:
            for token_str in tokens:
                handle.write(f"{token_str}\t{label}\n")
        handle.write("\n")


def build_dataset(code_root, report_path, labels_data, output_dir):
    report_entries = _load_json(report_path)
    smell_schemes = labels_data["smell_schemes"]
    name_to_slug = labels_data["slug_map"]
    global scheme_labels
    scheme_labels = labels_data["schemes"]

    code_root = os.path.abspath(code_root)
    samples_root = os.path.abspath(os.path.join(code_root, os.pardir))
    spans_by_smell = _build_smell_spans(report_entries, smell_schemes, name_to_slug, code_root)
    all_files = sorted(_iter_code_files(code_root))
    all_smells = sorted(smell_schemes.keys())
    full_file_smells = {"high-fan-in", "scattered-functionality"}
    full_file_by_smell = {slug: set() for slug in full_file_smells}

    normalized_name_to_slug = {
        _normalize_name(name): slug
        for name, slug in name_to_slug.items()
    }
    for entry in report_entries:
        name = _get_value(entry, "name", "Name")
        if not name:
            continue
        slug = name_to_slug.get(name) or normalized_name_to_slug.get(_normalize_name(name))
        if slug not in full_file_smells:
            continue
        file_path = _get_value(entry, "file_path", "File")
        if not file_path:
            continue
        normalized_path = _normalize_path(file_path, code_root)
        if normalized_path:
            full_file_by_smell[slug].add(normalized_path)

    positive_dir = os.path.join(output_dir, "positive")
    negative_dir = os.path.join(output_dir, "negative")
    os.makedirs(positive_dir, exist_ok=True)
    os.makedirs(negative_dir, exist_ok=True)

    for slug in all_smells:
        spans = spans_by_smell.get(slug, [])
        spans_by_file = {}
        for file_path, start, end, label_type in spans:
            spans_by_file.setdefault(file_path, []).append((start, end, label_type))
        scheme = smell_schemes.get(slug, "A")
        target_dir = positive_dir if spans else negative_dir
        output_path = os.path.join(target_dir, f"{slug}.conll")
        with open(output_path, "w", encoding="utf-8") as handle:
            for file_path in all_files:
                content = _read_file(file_path)
                display_path = file_path
                try:
                    common_root = os.path.commonpath([samples_root, file_path])
                except ValueError:
                    common_root = ""
                if common_root == samples_root:
                    display_path = os.path.relpath(file_path, samples_root)
                file_spans = spans_by_file.get(file_path, [])
                label_full_file = file_path in full_file_by_smell.get(slug, set())
                _write_conll(
                    handle,
                    display_path,
                    content,
                    file_spans,
                    scheme_labels[scheme],
                    label_full_file=label_full_file,
                )


def main():
    parser = argparse.ArgumentParser(description="Build per-smell CoNLL datasets from source code and a PyExamine report.")
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--report", required=True, help="Path to code_quality_report.json")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    output_dir = args.output_dir or _default_output_dir(args.code_path)
    build_dataset(args.code_path, args.report, LABELS, output_dir)


if __name__ == "__main__":
    main()
