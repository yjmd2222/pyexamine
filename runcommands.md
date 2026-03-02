# Analyze
python -m code_quality_analyzer.main samples --config code_quality_config_new.yaml --output code_quality_report.json

mkdir -p reports
for d in samples/*/; do
  name="$(basename "$d")"
  python -m code_quality_analyzer.main "$d" \
    --config code_quality_config_new.yaml \
    --output "reports/${name}.json"
done

# Canonical CoNLL (per project)
mkdir -p cdatasets
for d in samples/*/; do
  name="$(basename "$d")"
  mkdir -p "cdatasets/${name}"
  python -m dataset_generator.build_role_section_excerpts "$d" \
    --report "creports/${name}.json" \
    --templates templates_with_roles.json \
    --output-conll "cdatasets/${name}/role_section_excerpts.line.conll" \
    --context-lines 3 \
    --label-granularity line \
    --slow-row-seconds 2
done

mkdir -p cdatasets
for d in samples_module_complexity/projects/*/; do
  name="$(basename "$d")"
  mkdir -p "cdatasets/${name}"
  python -m dataset_generator.build_module_complexity_excerpts "$d" \
    --report "creports_module_complexity/${name}.module_complexity_report.json" \
    --output-conll "cdatasets/${name}/role_section_excerpts.line.conll" \
    --context-lines 3 \
    --label-granularity line
done

# CoNLL Load (manifest for notebook)
python -m training_inference.generate_conll_dataset_paths_config \
  --repo-root . \
  --dataset-root-dir cdatasets \
  --conll-name role_section_excerpts.line.conll \
  --output training_inference/conll_dataset_paths.config.json
