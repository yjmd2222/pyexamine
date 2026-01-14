# Dataset Commands

## Generate Per-Topic Datasets

```bash
for d in ./samples/*/; do
  name="$(basename "$d")"
  report="reports/${name}.json"
  outdir="datasets/${name}"
  mkdir -p "$outdir"

  python -m pyexamine smell_dataset "$d" --config code_quality_config_new.yaml --report "$report" --output-dir "$outdir"
done
```

## Build Smell Index From Reports

```bash
python -m pyexamine build_smell_index samples \
  --config code_quality_config_new.yaml \
  --report reports \
  --output samples/smell_index.json
```
