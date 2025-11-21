"""
Merge guidance into the repository's `bad_smells_info.json`.

This script will:
- Read `bad_smells_info.json` from the repository root.
- Read guidance generated at `writing_resource_file/bad_smells_info_with_guidance.json`.
- For each smell/metric in the repo JSON:
  - Remove `detection.module` (not meaningful without source files).
  - Replace `detection.summary` with an expanded summary composed from the
    guidance: definition, calculation, impact, mitigation, and references.
- Write the updated JSON back to the repository root (overwrites) and also
  write a copy into `writing_resource_file/bad_smells_info_expanded.json`.

Usage (from repo root):

    python writing_resource_file/scripts/merge_guidance_into_repo_json.py

NOTE: This script overwrites `bad_smells_info.json` in the repo root. It is
idempotent (running it multiple times produces the same output), but consider
committing or backing up the current JSON before running in critical contexts.
"""
from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_JSON = REPO_ROOT / 'bad_smells_info.json'
GUIDANCE_JSON = Path(__file__).resolve().parents[1] / 'bad_smells_info_with_guidance.json'
OUT_COPY = Path(__file__).resolve().parents[1] / 'bad_smells_info_expanded.json'

# Additional web references we fetched to include in summaries
ADDITIONAL_REFS = [
    {'title': 'Code Smell (Martin Fowler)', 'url': 'https://martinfowler.com/bliki/CodeSmell.html'},
    {'title': 'Code smell (Wikipedia)', 'url': 'https://en.wikipedia.org/wiki/Code_smell'},
    # Refactoring.guru had a 404 for the path used; include site root as general ref
    {'title': 'Refactoring.Guru', 'url': 'https://refactoring.guru/'}
]


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f'File not found: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def build_expanded_summary(original_summary: str, guidance: dict) -> str:
    parts = []
    if original_summary:
        parts.append(f"Original detector summary: {original_summary}")
    # Definition
    if guidance.get('definition'):
        parts.append(f"Definition: {guidance['definition']}")
    # Calculation
    if guidance.get('calculation'):
        parts.append(f"Calculation: {guidance['calculation']}")
    # Impact
    if guidance.get('impact'):
        parts.append(f"Impact: {guidance['impact']}")
    # Mitigation
    if guidance.get('mitigation'):
        parts.append(f"Mitigation: {guidance['mitigation']}")
    # References (guidance-level)
    refs = guidance.get('references', [])
    ref_lines = []
    for r in refs:
        if isinstance(r, dict):
            title = r.get('title') or r.get('note') or r.get('url')
            url = r.get('url')
            if url:
                ref_lines.append(f"- {title}: {url}")
            else:
                ref_lines.append(f"- {title}")
        else:
            ref_lines.append(f"- {str(r)}")
    # include additional fetched refs
    for r in ADDITIONAL_REFS:
        ref_lines.append(f"- {r['title']}: {r['url']}")
    if ref_lines:
        parts.append('References:\n' + '\n'.join(ref_lines))

    return '\n\n'.join(parts)


def main():
    repo = load_json(REPO_JSON)
    guidance_data = load_json(GUIDANCE_JSON)

    # Build guidance_map by name
    guidance_map = guidance_data.get('guidance_index', {})
    # Some guidance entries may be under metrics list; fallback
    if not guidance_map:
        guidance_map = {m['name']: m.get('guidance', {}) for m in guidance_data.get('metrics', [])}

    top_key = 'metrics' if 'metrics' in repo else 'smells' if 'smells' in repo else None
    if not top_key:
        print('No top-level metrics/smells key found in repo JSON')
        return 1

    updated = False
    for m in repo[top_key]:
        name = m.get('name')
        det = m.get('detection', {})
        original_summary = det.get('summary', '')
        # find guidance by name
        guidance = guidance_map.get(name) or guidance_map.get(name.lower()) or {}
        expanded = build_expanded_summary(original_summary, guidance)
        if expanded:
            m.setdefault('detection', {})['summary'] = expanded
            updated = True
        # remove module key if present
        if 'module' in m.get('detection', {}):
            del m['detection']['module']
            updated = True

    if updated:
        # write back to repo root (overwrite)
        REPO_JSON.write_text(json.dumps(repo, indent=2, ensure_ascii=False), encoding='utf-8')
        # also write a copy into writing_resource_file
        OUT_COPY.write_text(json.dumps(repo, indent=2, ensure_ascii=False), encoding='utf-8')
        print('Updated repo JSON and wrote copy to', OUT_COPY)
    else:
        print('No changes made to repo JSON')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
