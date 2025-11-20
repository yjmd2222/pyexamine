"""
Copy of converter that normalizes per-smell uppercase keys into a `metric_parameters` list.
This copy operates on `bad_smells_info.json` at repo root and writes a copy into this folder.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'bad_smells_info.json'
OUTPUT = Path(__file__).resolve().parents[1] / 'bad_smells_info.json'

UPPER_KEY_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789')


def looks_like_param_key(k):
    return all(c in UPPER_KEY_CHARS for c in k)


def normalize_smell(smell):
    if 'metric_parameters' in smell and isinstance(smell['metric_parameters'], list):
        return smell
    params = []
    # capture uppercase keys
    for k in list(smell.keys()):
        if looks_like_param_key(k):
            val = smell.pop(k)
            if isinstance(val, dict) and 'value' in val:
                params.append({
                    'parameter_name': k,
                    'value': val.get('value'),
                    'explanation': val.get('explanation')
                })
            else:
                params.append({'parameter_name': k, 'value': val, 'explanation': ''})
    if params:
        smell['metric_parameters'] = params
    return smell


def main():
    if not INPUT.exists():
        print('Input JSON not found:', INPUT)
        return
    j = json.loads(INPUT.read_text(encoding='utf-8'))
    top_key = 'smells' if 'smells' in j else 'metrics' if 'metrics' in j else None
    if not top_key:
        print('No smells/metrics top-level key found in', INPUT)
        return
    out_list = [normalize_smell(s) for s in j[top_key]]
    out = {'metrics': out_list}
    OUTPUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Wrote normalized copy to', OUTPUT)


if __name__ == '__main__':
    main()
