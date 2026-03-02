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
  --context-lines 3 \
  --label-granularity line \
  --slow-row-seconds 2

python -m dataset_generator.build_role_section_excerpts samples \
  --report code_quality_report.json \
  --templates templates_with_roles.json \
  --output-jsonl role_section_excerpts.token.jsonl \
  --context-lines 3 \
  --label-granularity token \
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
    --context-lines 3 \
    --label-granularity token \
    --slow-row-seconds 2
done

# module complexity (per project)
mkdir -p reports_module_complexity
for d in samples_module_complexity/projects/*/; do
  name="$(basename "$d")"
  python -m dataset_generator.build_module_complexity_report "$d" \
    --output-dir "reports_module_complexity"
done

mkdir -p datasets
for d in samples_module_complexity/projects/*/; do
  name="$(basename "$d")"
  mkdir -p "datasets/${name}"
  python -m dataset_generator.build_module_complexity_excerpts "$d" \
    --report "reports_module_complexity/${name}.module_complexity_report.json" \
    --output-jsonl "datasets/${name}/role_section_excerpts.line.jsonl" \
    --context-lines 3 \
    --label-granularity line
done

mkdir -p datasets
for d in samples_module_complexity/projects/*/; do
  name="$(basename "$d")"
  mkdir -p "datasets/${name}"
  python -m dataset_generator.build_module_complexity_excerpts "$d" \
    --report "reports_module_complexity/${name}.module_complexity_report.json" \
    --output-jsonl "datasets/${name}/role_section_excerpts.token.jsonl" \
    --context-lines 3 \
    --label-granularity token
done

# Load
python -m training_inference.generate_dataset_paths_config \
  --repo-root . \
  --dataset-root-dir datasets \
  --excerpt-name role_section_excerpts.line.jsonl \
  --output training_inference/dataset_paths.config46AndComplexity.json

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
