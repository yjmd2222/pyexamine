# training_inference

Notebook-first training/inference scaffold for **shared encoder + 46 smell-specific token heads**.

## Files

- `model_pipeline.py` — shared encoder + routed 46-head token classification model
- `data_utils.py` — JSONL loading, deterministic splits, balancing, pretokenized label alignment
- `train_loop.py` — train/eval loops, checkpoints, debug previews, reproducibility
- `inference_utils.py` — batched inference JSONL outputs keyed by `id`
- `checkpoint_utils.py` — rebuild/load model from checkpoint metadata
- `train_modernbert_routed_46heads.ipynb` — training notebook
- `infer_modernbert_routed_46heads.ipynb` — inference notebook

## Notes

- The code prefers `role_section_excerpts.line.jsonl`, and falls back to `role_section_excerpts.jsonl` if the line file is not present.
- `role_section_excerpts.sidecar.jsonl` is intentionally **not** used yet (placeholder comments are included for future join-by-`id`).
- Right truncation is used, which means sequences over the max length are truncated **from the end**.
