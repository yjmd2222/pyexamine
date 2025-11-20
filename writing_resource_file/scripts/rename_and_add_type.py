"""
Copy of rename/type script to operate on the repo JSON and write a copy into this folder.
It renames `smells` to `metrics` if present and adds a `type` inferred from `detection.module`.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'bad_smells_info.json'
OUTPUT = Path(__file__).resolve().parents[1] / 'bad_smells_info.json'


def infer_type(module_name):
    if not module_name:
        return 'code_smell'
    if 'architectural' in module_name:
        return 'architectural_smell'
    if 'structural' in module_name:
        return 'structural_smell'
    if 'code_smell' in module_name or 'code' in module_name:
        return 'code_smell'
    return 'code_smell'


def main():
    if not INPUT.exists():
        print('Input JSON not found:', INPUT)
        return
    j = json.loads(INPUT.read_text(encoding='utf-8'))
    top_key = 'smells' if 'smells' in j else 'metrics' if 'metrics' in j else None
    if not top_key:
        print('No smells/metrics top-level key found in', INPUT)
        return
    metrics = j[top_key]
    for m in metrics:
        module = m.get('detection', {}).get('module')
        m['type'] = infer_type(module)
    out = {'metrics': metrics}
    OUTPUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Wrote typed copy to', OUTPUT)


if __name__ == '__main__':
    main()
