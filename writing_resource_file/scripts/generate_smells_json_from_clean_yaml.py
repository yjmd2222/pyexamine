"""
Copy of the generator: builds JSON from a clean YAML and detector sources.
Note: This copy is intended to be a stable helper inside the resource folder.
"""
import re
import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src' / 'code_quality_analyzer'
INPUT_YAML = ROOT / 'bad_smells_info.yaml'
OUTPUT_JSON = ROOT / 'bad_smells_info.json'

DETECTOR_FILES = list(SRC.glob('*_detector.py'))


def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_implementation(module_path, function_name):
    text = module_path.read_text(encoding='utf-8')
    # simple regex to capture def <function_name>(...):\n    # and following indented block
    pattern = re.compile(r"def\s+" + re.escape(function_name) + r"\s*\([^)]*\):\n(\s+.+(?:\n\s+.+)*)", re.M)
    m = pattern.search(text)
    if m:
        return m.group(0)
    return ''


def build_json(yaml_data):
    smells = []
    for cat, items in yaml_data.items():
        for name, props in items.items():
            smell = {
                'name': name,
                'id': props.get('id'),
                'detection': {
                    'function': props.get('detection', {}).get('function'),
                    'module': props.get('detection', {}).get('module'),
                    'language': 'python',
                    'summary': props.get('detection', {}).get('summary'),
                    'type': props.get('detection', {}).get('type')
                }
            }
            fn = smell['detection'].get('function')
            mod = smell['detection'].get('module')
            if fn and mod:
                # try to find module file
                mod_file = SRC / (mod + '.py')
                if mod_file.exists():
                    smell['detection']['implementation'] = extract_implementation(mod_file, fn)
            # include the rest of props (parameters etc.)
            smell.update({k: v for k, v in props.items() if k != 'detection'})
            smells.append(smell)
    return {'smells': smells}


def main():
    if not INPUT_YAML.exists():
        print('Input YAML not found:', INPUT_YAML)
        return
    yaml_data = read_yaml(INPUT_YAML)
    out = build_json(yaml_data)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print('Wrote', OUTPUT_JSON)


if __name__ == '__main__':
    main()
