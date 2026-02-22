# Active Command Scope

## User-Confirmed Commands (only)

1. `python -m code_quality_analyzer.main`
2. `python -m dataset_generator.build_role_section_excerpts`

These are the only commands to use for this workflow.

## Canonical Examples

```bash
python -m code_quality_analyzer.main samples --config code_quality_config_new.yaml --output code_quality_report.json
```

```bash
python -m dataset_generator.build_role_section_excerpts samples --report code_quality_report.json --templates templates_with_roles.json --output-jsonl role_section_excerpts.jsonl --output-sidecar-jsonl role_section_excerpts.sidecar.jsonl
```

## Out of Scope

- `python -m pyexamine analyze ...`
- `python -m pyexamine smell_dataset ...`
- `python -m pyexamine build_smell_index ...`
- `python -m dataset_generator.build_detr_dataset ...`
- `python -m dataset_generator.build_excerpts ...`

Reason: user explicitly constrained operational commands to the two commands above.
