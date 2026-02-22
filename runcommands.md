# Analyze
python -m code_quality_analyzer.main samples  --config code_quality_config_new.yaml --output code_quality_report.json

for d in samples/*/; do
  name="$(basename "$d")"
  mkdir -p "reports/${name}"
  python -m code_quality_analyzer.main "$d" \
    --config code_quality_config_new.yaml \
    --output "reports/${name}/code_quality_report.json"
done

# excerpt
python -m dataset_generator.build_role_section_excerpts samples --report code_quality_report.json --templates templates_with_roles.json --output-jsonl role_section_excerpts.jsonl --output-sidecar-jsonl role_section_excerpts.sidecar.jsonl --context-lines 3 --label-granularity line

for d in samples/*/; do
  name="$(basename "$d")"
  python -m dataset_generator.build_role_section_excerpts "$d" \
    --report "reports/${name}.json" \
    --templates templates_with_roles.json \
    --output-jsonl "datasets/${name}/role_section_excerpts.jsonl" \
    --output-sidecar-jsonl "datasets/${name}/role_section_excerpts.sidecar.jsonl" \
    --context-lines 3 \
    --label-granularity line
done

python -m dataset_generator.build_role_section_excerpts samples \
  --report code_quality_report.json \
  --templates templates_with_roles.json \
  --output-jsonl role_section_excerpts.jsonl \
  --output-sidecar-jsonl role_section_excerpts.sidecar.jsonl \
  --context-lines 3 \
  --label-granularity token
