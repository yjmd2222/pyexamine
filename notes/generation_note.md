# Generation Note

Report and excerpt generation can take a long time on the expanded sample set.

Observed behavior:
- Report generation is generally fast enough per project.
- Excerpt generation (`build_role_section_excerpts`) is the expensive step.
- Large projects can require several minutes each (line and token both), especially with sidecar output.

Practical guidance:
- Use long timeout values for excerpt generation (>= 10 minutes per project for large projects).
- Run per-project generation with progress logs so it does not look stuck.
- Avoid short global timeouts; global token+sidecar generation can exceed common CI defaults.

Verification checks for correct excerpt generation:
- `report vs excerpt is_detected counts`:
  - Count detected entries in report (`is_detected=true` equivalent: number of report rows).
  - Count `is_detected=true` rows in generated excerpt JSONL.
  - These counts must match for global and per-project outputs.
- `line vs token evidence entity count`:
  - Compare evidence entity count between line and token outputs using `B-*` labels as entity starts.
  - Token granularity must satisfy: `B_token >= B_line` (overall and per smell/project).
