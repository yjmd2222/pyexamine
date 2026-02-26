# training_inference

Notebook-first training/inference scaffold for **shared encoder + 46 smell-specific token heads**.

## Files

- `model_pipeline.py` - shared encoder + routed 46-head token classification model
- `data_utils.py` - JSONL loading, deterministic splits, balancing, pretokenized label alignment
- `train_loop.py` - train/eval loops, checkpoints, debug previews, reproducibility
- `inference_utils.py` - batched inference JSONL outputs keyed by `id`
- `checkpoint_utils.py` - rebuild/load model from checkpoint metadata
- `generate_dataset_paths_config.py` - helper CLI to generate dataset path config JSON
- `train_modernbert_routed_46heads.ipynb` - training notebook
- `infer_modernbert_routed_46heads.ipynb` - inference notebook

## Notes

- If `datasets/*/role_section_excerpts.line.jsonl` exists, dataset loading prefers per-project files and merges them.
- Otherwise it falls back to root single-file mode:
  - preferred: `role_section_excerpts.line.jsonl`
  - fallback: `role_section_excerpts.jsonl`
- You can pin explicit input files by config:
  - generate config: `python -m training_inference.generate_dataset_paths_config --repo-root . --output training_inference/dataset_paths.config.json`
  - pass to loader: `create_dataset_build(..., dataset_config_path=Path("training_inference/dataset_paths.config.json"))`
- `role_section_excerpts.sidecar.jsonl` is intentionally **not** used yet (placeholder comments are included for future join-by-`id`).
- Right truncation is used, which means sequences over the max length are truncated **from the end**.
