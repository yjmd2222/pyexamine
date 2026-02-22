# Analyze
python -m pyexamine analyze samples --config code_quality_config_new.yaml --output code_quality_report.json
python -m code_quality_analyzer.main samples  --config code_quality_config_new.yaml --output code_quality_report.json

# excerpt
python -m dataset_generator.build_role_section_excerpts samples --report code_quality_report.json --templates templates_with_roles.json --output-jsonl role_section_excerpts.jsonl --output-sidecar-jsonl role_section_excerpts.sidecar.jsonl
