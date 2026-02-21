# Analyze
python -m pyexamine analyze samples --config code_quality_config_new.yaml --output code_quality_report.json
python -m code_quality_analyzer.main samples  --config code_quality_config_new.yaml -- code_quality_report.json

# Candidate detr
python -m dataset_generator.build_detr_candidates samples --config code_quality_config_new.yaml --output detr_candidates.json

# DEPR
Deprecation indicating section

# Dataset commands
python -m dataset_generator.build_detr_dataset samples --report code_quality_report.json --output code_quality_report_detr.json

# Excerpt command
python -m dataset_generator.build_excerpts --detr code_quality_report_detr.json --output code_quality_report_excerpts.json

# Role-section excerpts (from candidate DETR)
python -m dataset_generator.build_role_section_excerpts --detr detr_candidates.json --output-jsonl role_section_excerpts.jsonl --output-sidecar-jsonl role_section_excerpts.sidecar.jsonl --tokenizer answerdotai/ModernBERT-large

# Dataset Commands (DEPR)

## Generate Per-Topic Datasets

```bash
for d in ./samples/*/; do
  name="$(basename "$d")"
  report="reports/${name}.json"
  metadata="reports/${name}_metadata.json"
  outdir="datasets/${name}"
  mkdir -p "$outdir"

  python -m pyexamine smell_dataset "$d" \
    --config code_quality_config_new.yaml \
    --report "$report" \
    --metadata-output "$metadata" \
    --output-dir "$outdir"
done
```

## Build Smell Index From Reports

```bash
python -m pyexamine build_smell_index samples \
  --config code_quality_config_new.yaml \
  --report reports \
  --output samples/smell_index.json \
  --no-analyze
```


## Generate DETR-style Dataset (Single JSON per Sample)

This outputs one file per sample directory:
- `datasets/<sample>/detr_dataset.json`

```bash
for d in ./samples/*/; do
  name="$(basename "$d")"
  report="reports/${name}.json"
  metadata="reports/${name}_metadata.json"
  outdir="datasets/${name}"
  mkdir -p "$outdir"

  python -m pyexamine smell_dataset "$d"         --config code_quality_config_new.yaml         --report "$report"         --metadata-output "$metadata"         --output-dir "$outdir"         --format detr
done
```
