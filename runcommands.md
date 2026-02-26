# Analyze
python -m code_quality_analyzer.main samples --config code_quality_config_new.yaml --output code_quality_report.json

mkdir -p reports
for d in samples/*/; do
  name="$(basename "$d")"
  python -m code_quality_analyzer.main "$d" \
    --config code_quality_config_new.yaml \
    --output "reports/${name}.json"
done

# Excerpts (global)
python -m dataset_generator.build_role_section_excerpts samples \
  --report code_quality_report.json \
  --templates templates_with_roles.json \
  --output-jsonl role_section_excerpts.line.jsonl \
  --output-sidecar-jsonl role_section_excerpts.line.sidecar.jsonl \
  --context-lines 3 \
  --label-granularity line
  --slow-row-seconds 2

python -m dataset_generator.build_role_section_excerpts samples \
  --report code_quality_report.json \
  --templates templates_with_roles.json \
  --output-jsonl role_section_excerpts.token.jsonl \
  --output-sidecar-jsonl role_section_excerpts.token.sidecar.jsonl \
  --context-lines 3 \
  --label-granularity token
  --slow-row-seconds 2

# Excerpts (per project)
mkdir -p datasets
for d in samples/*/; do
  name="$(basename "$d")"
  mkdir -p "datasets/${name}"
  python -m dataset_generator.build_role_section_excerpts "$d" \
    --report "reports/${name}.json" \
    --templates templates_with_roles.json \
    --output-jsonl "datasets/${name}/role_section_excerpts.line.jsonl" \
    --output-sidecar-jsonl "datasets/${name}/role_section_excerpts.line.sidecar.jsonl" \
    --context-lines 3 \
    --label-granularity line \
    --slow-row-seconds 2
done


mkdir -p datasets
for d in samples/*/; do
  name="$(basename "$d")"
  mkdir -p "datasets/${name}"
  python -m dataset_generator.build_role_section_excerpts "$d" \
    --report "reports/${name}.json" \
    --templates templates_with_roles.json \
    --output-jsonl "datasets/${name}/role_section_excerpts.token.jsonl" \
    --output-sidecar-jsonl "datasets/${name}/role_section_excerpts.token.sidecar.jsonl" \
    --context-lines 3 \
    --label-granularity token \
    --slow-row-seconds 2
done

# Load
python -m training_inference.generate_dataset_paths_config \
  --repo-root . \
  --dataset-root-dir datasets \
  --excerpt-name role_section_excerpts.line.jsonl \
  --sidecar-name role_section_excerpts.line.sidecar.jsonl \
  --output training_inference/dataset_paths.config.json
