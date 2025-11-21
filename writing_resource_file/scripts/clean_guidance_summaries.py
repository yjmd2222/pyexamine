#!/usr/bin/env python3
"""
clean_guidance_summaries.py

Read the repo-root `bad_smells_info.json` and replace each metric's
`detection.summary` string with a standardized, concise, structured text:

- Summary: one-line about what the detector does
- Definition: concise definition of the smell
- Calculation: step-by-step how the metric is computed and compared to thresholds
- Impact / Mitigation / References: summarized from existing content when available

The script writes a backup `bad_smells_info.json.bak` before overwriting.
"""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / 'bad_smells_info.json'
BACKUP_PATH = ROOT / 'bad_smells_info.json.bak'


def extract_thresholds(metric):
    params = metric.get('metric_parameters', [])
    mapping = {p.get('parameter_name'): p.get('value') for p in params}
    return mapping


def impl_heuristic(impl_text):
    """Return a brief action description inferred from implementation text."""
    text = impl_text or ''
    # heuristics in order
    if ('actual_lines' in text and 'LONG_METHOD' in text) or ('actual_lines' in text and 'lines' in text):
        return 'Counts non-empty, non-comment lines in each function and flags methods exceeding the configured line threshold.'
    if 'non_trivial_methods' in text or 'LARGE_CLASS_METHODS' in text:
        return 'Counts non-trivial instance methods of each class and flags classes with too many methods.'
    if 'primitive' in text and 'parameters' in text:
        return 'Looks for functions that accept many primitive-typed parameters and flags those with a high primitive-parameter ratio.'
    if 'len(args)' in text or 'LONG_PARAMETER_LIST' in text:
        return 'Counts positional parameters of each function (excluding `self`) and flags functions with too many parameters.'
    if 'parameter_groups' in text or 'DATA_CLUMPS' in text:
        return 'Finds parameter name combinations that co-occur across multiple functions (data clumps).'
    if 'COMPLEX_CONDITIONAL' in text or 'count_conditions' in text:
        return 'Detects conditionals with many branches (if/elif chains) that resemble switch-like statements.'
    if 'TEMPORARY_FIELD' in text or 'init_fields' in text:
        return 'Detects instance fields assigned in __init__ but rarely used elsewhere (temporary fields).'
    if 'Duplicate Code' in text or 'normalize_code' in text:
        return 'Normalizes function bodies and detects similar code blocks across functions (duplicate code).'
    # fallback
    return 'Analyzes AST nodes in the module and reports occurrences of the named smell according to configured thresholds.'


def build_summary(metric):
    name = metric.get('name')
    fn = metric.get('detection', {}).get('function')
    impl = metric.get('detection', {}).get('implementation', '')
    params = extract_thresholds(metric)

    summary_line = impl_heuristic(impl)

    # Definition: concise
    definition = f"{name}: a code pattern that makes code harder to understand, test, or maintain."
    # Try to be more specific for common smells
    specific_defs = {
        'Long Method': 'A function or method that has too many executable lines, increasing complexity and reducing readability.',
        'Large Class': 'A class that contains an excessive number of meaningful methods, indicating low cohesion or multiple responsibilities.',
        'Long Parameter List': 'A function with many parameters, which makes it hard to understand and use; often indicates missing abstraction or parameter object.',
        'Data Clumps': 'Groups of parameters that frequently occur together across different functions, suggesting they should be encapsulated in a single object.',
        'Primitive Obsession': 'Overuse of primitive types for related data instead of domain-specific small objects or enums.',
    }
    if name in specific_defs:
        definition = specific_defs[name]

    # Calculation: build from patterns and metric_parameters
    calc_lines = []
    # Common patterns
    if 'Lines' in ','.join(params.keys()) or 'LONG_METHOD_LINES' in params:
        v = params.get('LONG_METHOD_LINES', params.get('LINES', None))
        if v is not None:
            calc_lines.append(f"Count non-empty, non-comment lines in a function; report a '{name}' if the count > {v}.")
    if 'LARGE_CLASS_METHODS' in params:
        calc_lines.append(f"Count non-trivial instance methods in a class (exclude magic and trivial getters/setters); report a '{name}' if count > {params['LARGE_CLASS_METHODS'] }.")
    if 'LONG_PARAMETER_LIST' in params:
        calc_lines.append(f"Count positional parameters (exclude `self`); report if count > {params['LONG_PARAMETER_LIST'] } (varargs may raise threshold by +2).")
    if 'PRIMITIVE_OBSESSION_COUNT' in params or 'PRIMITIVE_MIN_ARGS' in params:
        c = params.get('PRIMITIVE_OBSESSION_COUNT')
        min_args = params.get('PRIMITIVE_MIN_ARGS')
        rr = params.get('PRIMITIVE_RATIO_THRESHOLD')
        parts = []
        if min_args is not None:
            parts.append(f"only applied when function has > {min_args} args")
        if c is not None:
            parts.append(f"flags when > {c} primitive parameters are present")
        if rr is not None:
            parts.append(f"and primitive-parameter ratio > {rr}")
        if parts:
            calc_lines.append("; ".join(parts).capitalize() + ".")
    # Fallback: try to extract comparison to self.thresholds[...] in implementation
    thresh_matches = re.findall(r"self\.thresholds\[\"([A-Z0-9_]+)\"\]", impl)
    for t in thresh_matches:
        if t in params:
            calc_lines.append(f"Uses threshold `{t}` = {params[t]} from configuration to decide when to report.")
        else:
            calc_lines.append(f"Uses threshold `{t}` from configuration.")

    if not calc_lines:
        calc_lines.append('See implementation: compute the metric from AST and compare against configured thresholds to decide reporting.')

    calculation = ' '.join(calc_lines)

    # Impact and mitigation: try to extract from existing summary if present
    existing_summary = metric.get('detection', {}).get('summary', '')
    impact = ''
    mitigation = ''
    refs = []
    if existing_summary:
        # simple heuristics: split by headings
        # Capture Impact:, Mitigation:, References:
        im = re.search(r'Impact:(.*?)(?:\n\n|Mitigation:|References:)', existing_summary, re.S)
        if im:
            impact = im.group(1).strip()
        mt = re.search(r'Mitigation:(.*?)(?:\n\n|References:)', existing_summary, re.S)
        if mt:
            mitigation = mt.group(1).strip()
        refs = re.findall(r'-\s*(https?://[^\n\r\s]+)', existing_summary)

    # Assemble new summary string
    parts = []
    parts.append(f"Summary: {summary_line}")
    parts.append(f"Definition: {definition}")
    parts.append(f"Calculation: {calculation}")
    if impact:
        parts.append(f"Impact: {impact}")
    if mitigation:
        parts.append(f"Mitigation: {mitigation}")
    if refs:
        parts.append("References: " + '; '.join(refs))

    return '\n\n'.join(parts)


def main():
    if not JSON_PATH.exists():
        print('ERROR: bad_smells_info.json not found at', JSON_PATH)
        return 2

    data = json.loads(JSON_PATH.read_text(encoding='utf-8'))
    # backup
    BACKUP_PATH.write_text(JSON_PATH.read_text(encoding='utf-8'), encoding='utf-8')

    metrics = data.get('metrics') or data.get('smells')
    if not metrics:
        print('No metrics found in JSON')
        return 1

    for m in metrics:
        # Build and set new summary
        new_summary = build_summary(m)
        if 'detection' not in m:
            m['detection'] = {}
        m['detection']['summary'] = new_summary

    # write back
    JSON_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Updated', JSON_PATH, 'and saved backup to', BACKUP_PATH)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
