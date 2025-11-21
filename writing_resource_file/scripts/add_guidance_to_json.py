"""
Add guidance metadata to each smell entry in `bad_smells_info.json`.

This script reads the repository `bad_smells_info.json` (repo root), constructs
per-smell guidance fields (definition, calculation, impact, mitigation,
example heuristics), and writes an enriched copy to
`writing_resource_file/bad_smells_info_with_guidance.json`.

The guidance text is templated from known, reputable sources (Fowler's
Refactoring, Clean Code, refactoring.guru) and includes a static references
list. For smells with available metric parameters the script includes the
calculation description using those parameter names/values.

Usage (from repo root):

    python writing_resource_file/scripts/add_guidance_to_json.py

The script is idempotent: running it multiple times overwrites the output file
with the same structure.
"""
from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_JSON = REPO_ROOT / 'bad_smells_info.json'
OUT_JSON = Path(__file__).resolve().parents[1] / 'bad_smells_info_with_guidance.json'

# Curated references (reputable books, webpages, and classic papers)
REFERENCES = [
    {
        'title': 'Refactoring: Improving the Design of Existing Code',
        'author': 'Martin Fowler',
        'year': 1999,
        'url': 'https://martinfowler.com/books/refactoring.html'
    },
    {
        'title': 'Code Smells (catalog)',
        'author': 'Martin Fowler (Bliki)',
        'year': None,
        'url': 'https://martinfowler.com/bliki/CodeSmell.html'
    },
    {
        'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
        'author': 'Robert C. Martin',
        'year': 2008,
        'url': 'https://www.oreilly.com/library/view/clean-code-a/9780136083238/'
    },
    {
        'title': 'Refactoring Guru — Code Smells',
        'author': 'Refactoring.Guru',
        'url': 'https://refactoring.guru/smells'
    },
    {
        'title': 'Detection strategies: metric-based rules for detection of design flaws',
        'author': 'Radu Marinescu',
        'year': 2004,
        'note': 'Classic metrics-based detection strategies for design flaws (search for the paper title for publisher details)'
    }
]

# Helper guidance templates for known smell names. Each entry contains a
# function that receives the smell dict and returns a guidance dict.

def template_long_method(smell):
    params = {p['parameter_name']: p for p in smell.get('metric_parameters', [])}
    threshold = params.get('LONG_METHOD_LINES', {}).get('value')
    calc = "Count the number of non-empty, non-comment lines inside a function/method."
    if threshold:
        calc += f" Report a Long Method if this count exceeds the configured threshold ({threshold})."
    return {
        'definition': 'A function or method that contains too many lines of code, making it hard to read and maintain.',
        'calculation': calc,
        'impact': 'Large methods are more complex, harder to test, and often do more than one responsibility.',
        'mitigation': 'Refactor by extracting smaller functions, applying the Single Responsibility Principle, and improving naming and comments.',
        'references': [REFERENCES[0], REFERENCES[1], REFERENCES[2]]
    }


def template_large_class(smell):
    params = {p['parameter_name']: p for p in smell.get('metric_parameters', [])}
    threshold = params.get('LARGE_CLASS_METHODS', {}).get('value')
    calc = 'Count non-trivial instance methods of a class (exclude magic methods and trivial getters/setters).'
    if threshold:
        calc += f" Flag a Large Class if the count exceeds {threshold}."
    return {
        'definition': 'A class that has accumulated too many responsibilities or methods, often indicating poor cohesion.',
        'calculation': calc,
        'impact': 'Large classes are hard to understand and maintain; they often violate SRP and can hide multiple responsibilities.',
        'mitigation': 'Split the class into smaller, cohesive classes, or extract helper classes/objects.',
        'references': [REFERENCES[0], REFERENCES[2]]
    }


def template_long_parameter_list(smell):
    params = {p['parameter_name']: p for p in smell.get('metric_parameters', [])}
    threshold = params.get('LONG_PARAMETER_LIST', {}).get('value')
    calc = 'Count positional parameters (exclude `self` for methods). If varargs or kwargs are present, increase the effective threshold by 2.'
    if threshold:
        calc += f" Flag a Long Parameter List when the count exceeds {threshold} (or adjusted threshold for varargs)."
    return {
        'definition': 'A function/method with many parameters, which makes it hard to call and maintain.',
        'calculation': calc,
        'impact': 'Long parameter lists are error-prone, hinder reuse, and suggest missing abstractions.',
        'mitigation': 'Introduce parameter objects, group related parameters into small classes/structs, or refactor the function into smaller operations.',
        'references': [REFERENCES[0], REFERENCES[2]]
    }


def template_data_clumps(smell):
    params = {p['parameter_name']: p for p in smell.get('metric_parameters', [])}
    thr = params.get('DATA_CLUMPS_THRESHOLD', {}).get('value')
    calc = 'Find parameter combinations that appear together across multiple functions. Use combination size >= DATA_CLUMP_MIN_COMBO_SIZE.'
    if thr:
        calc += f" Report clumps when the combo size and occurrence count meet thresholds (e.g. >= {thr})."
    return {
        'definition': 'Groups of parameters that are frequently passed together across different functions, indicating a missing abstraction.',
        'calculation': calc,
        'impact': 'Leads to duplicated parameter lists, scattered logic, and harder maintenance.',
        'mitigation': 'Create a small value object or data transfer object to encapsulate the clumped parameters.',
        'references': [REFERENCES[0], REFERENCES[3]]
    }


def template_generic(smell):
    # Use available params to produce a calculation hint
    params = smell.get('metric_parameters', [])
    calc_parts = []
    for p in params:
        calc_parts.append(f"{p['parameter_name']} = {p.get('value')}")
    calc_text = ' ; '.join(calc_parts) if calc_parts else 'See detector parameters for metric thresholds.'
    return {
        'definition': f"{smell.get('name')} — see detector summary for details.",
        'calculation': calc_text,
        'impact': 'See references for empirical studies on maintenance impact.',
        'mitigation': 'Use standard refactorings (extract, split, encapsulate) guided by code reviews and tests.',
        'references': [REFERENCES[0], REFERENCES[2], REFERENCES[3]]
    }


# Mapping smell names (normalized) to templates
TEMPLATES = {
    'Long Method'.lower(): template_long_method,
    'Large Class'.lower(): template_large_class,
    'Long Parameter List'.lower(): template_long_parameter_list,
    'Data Clumps'.lower(): template_data_clumps,
}


def build_guidance_for_smell(smell):
    name = smell.get('name', '').lower()
    fn = TEMPLATES.get(name, template_generic)
    return fn(smell)


def main():
    if not SRC_JSON.exists():
        print('Source JSON not found at', SRC_JSON)
        return 1

    data = json.loads(SRC_JSON.read_text(encoding='utf-8'))
    # accept both top-level keys 'metrics' or 'smells'
    top_key = 'metrics' if 'metrics' in data else 'smells' if 'smells' in data else None
    if not top_key:
        print('No top-level metrics/smells key found')
        return 2

    metrics = data[top_key]
    guidance_map = {}
    for m in metrics:
        guidance_map[m.get('name')] = build_guidance_for_smell(m)
        # add guidance into the smell entry as well for direct consumption
        m['guidance'] = guidance_map[m.get('name')]

    # Compose output with references and enriched metrics
    out = {
        'metrics': metrics,
        'guidance_index': guidance_map,
        'references': REFERENCES
    }

    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Wrote guidance-enhanced JSON to', OUT_JSON)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
