# Active Command Scope

## Current Workflow Commands

The commands currently used in `runcommands.md` are:

1. `python -m code_quality_analyzer.main`
2. `python -m dataset_generator.build_role_section_excerpts`
3. `python -m dataset_generator.build_module_complexity_report`
4. `python -m dataset_generator.build_module_complexity_excerpts`
5. `python -m training_inference.generate_dataset_paths_config`

## Canonical Usage Shape

### 46 smells
- Analyze:
  - global: run `code_quality_analyzer.main` on `samples`
  - per project: loop over `samples/*/`
- Excerpts:
  - global: run `build_role_section_excerpts` on `samples`
  - per project: loop over `samples/*/`
- Load:
  - generate dataset-path config from `datasets`

### Module complexity
- Reports:
  - per project only: loop over `samples_module_complexity/projects/*/`
  - use `build_module_complexity_report` with positional project path
- Excerpts:
  - per project only: loop over `samples_module_complexity/projects/*/`
  - use `build_module_complexity_excerpts`
- Load:
  - generate dataset-path config from `datasets_module_complexity`

## Canonical Examples

```bash
python -m code_quality_analyzer.main samples --config code_quality_config_new.yaml --output code_quality_report.json
```

```bash
python -m dataset_generator.build_role_section_excerpts samples --report code_quality_report.json --templates templates_with_roles.json --output-jsonl role_section_excerpts.line.jsonl --output-sidecar-jsonl role_section_excerpts.line.sidecar.jsonl --context-lines 3 --label-granularity line
```

```bash
python -m dataset_generator.build_module_complexity_report samples_module_complexity/projects/harbor_manifest --output-dir reports_module_complexity
```

```bash
python -m dataset_generator.build_module_complexity_excerpts samples_module_complexity/projects/harbor_manifest --report reports_module_complexity/harbor_manifest.module_complexity_report.json --output-jsonl datasets_module_complexity/harbor_manifest/role_section_excerpts.line.jsonl --output-sidecar-jsonl datasets_module_complexity/harbor_manifest/role_section_excerpts.line.sidecar.jsonl --context-lines 3 --label-granularity line
```

```bash
python -m training_inference.generate_dataset_paths_config --repo-root . --dataset-root-dir datasets --excerpt-name role_section_excerpts.line.jsonl --sidecar-name role_section_excerpts.line.sidecar.jsonl --output training_inference/dataset_paths.config.json
```

## Out of Scope

- `python -m pyexamine analyze ...`
- `python -m pyexamine smell_dataset ...`
- `python -m pyexamine build_smell_index ...`
- `python -m dataset_generator.build_detr_dataset ...`
- `python -m dataset_generator.build_excerpts ...`
- `python -m dataset_generator.merge_reports ...`

Reason: these are not part of the current documented workflow in `runcommands.md`.
