# Work Summary: DIT/Scattered Role + Report/Excerpt Alignment

## Scope
- Aligned contributor-role extraction and role templates with `code_quality_report.json` structure.
- Fixed `Deep Inheritance Tree (DIT)` and `Scattered Functionality` to carry root identity lines (`start_line_number` / `end_line_number`) instead of WHOLE_FILE-style ROLE0 behavior.
- Kept excerpt formatting/token conventions aligned with existing role-section format (`[ROLE0]`, `[FILE]`, `path=...`, `[SEP_EXCERPT]`, etc.).

## What Was Updated

### 1) Detector/report payload generation
- `src/code_quality_analyzer/structural_smell_detector.py`
  - `detect_dit` now sets root identity `start_line_number/end_line_number` from target class info.
- `src/code_quality_analyzer/architectural_smell_detector.py`
  - `detect_scattered_functionality` now sets root identity `start_line_number/end_line_number` from the selected anchor function span.
- `src/code_quality_analyzer/smell_templates.py`
  - Connected payload dataclasses used by DIT/Scattered now support optional root identity line fields.
- `src/code_quality_analyzer/main.py`
  - Report export backfills payload root line numbers from smell object if missing.
  - For DIT/Scattered, JSON key order is normalized so root identity lines appear before `files` evidence block (consistency with other smells).

### 2) Role template updates
- Updated both:
  - `master-thesis-materials/data/templates_with_roles.json`
  - `master-thesis-materials/pyexamine/templates_with_roles.json`
- For both smells:
  - `Deep Inheritance Tree (DIT)`
  - `Scattered Functionality`
- `ROLE0.line_source` changed to:
  - `start_line_number/end_line_number`
  - (instead of `WHOLE_FILE`)

### 3) Excerpt-generation behavior confirmed
- Overlap handling:
  - Within a role: spans are expanded+merged per file.
  - Across roles: no cross-role dedup; overlap can appear in multiple role sections.
- Empty-role behavior:
  - Role tags remain, but no `[FILE]` block is emitted when role spans are empty.

## Important Correction Made During Fix
- A temporary dataclass-field reorder caused:
  - `TypeError: non-default argument 'files' follows default argument`
- Resolved by restoring valid dataclass field order and moving ordering control to report serialization logic in `main.py`.

## Commands (final/valid)

### Report generation
```bash
/c/Users/jinmo/miniconda3/envs/yjmd2222-pyexamine/python -m code_quality_analyzer.main samples --config code_quality_config_new.yaml --output code_quality_report.json
```

### Role-section excerpt generation
```bash
/c/Users/jinmo/miniconda3/envs/yjmd2222-pyexamine/python -m dataset_generator.build_role_section_excerpts samples --report code_quality_report.json --templates templates_with_roles.json --output-jsonl role_section_excerpts.jsonl --output-sidecar-jsonl role_section_excerpts.sidecar.jsonl
```

