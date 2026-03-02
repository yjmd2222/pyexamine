# Strict Dataset Structure

The training/inference dataset config helper now enforces this structure:

`datasets/<individual_dataset>/excerpt.jsonl`

Rules:

- Refer to [runcommands.md](../runcommands.md) for `Analyze`, `Excerpts`, and `Load`. The former two must be prepared before `Load`.
- `--dataset-root-dir` points to the parent directory (`datasets`).
- Every child dataset directory must contain `excerpt.jsonl`.
- No fallback names are used in strict mode.
- If any dataset directory is missing the excerpt file, config generation fails.

Generate config:

```bash
python -m training_inference.generate_dataset_paths_config \
  --repo-root . \
  --dataset-root-dir datasets \
  --excerpt-name excerpt.jsonl \
  --output training_inference/dataset_paths.config.json
```

Use in code:

```python
from pathlib import Path
from training_inference.data_utils import create_dataset_build

dataset_build = create_dataset_build(
    repo_root=Path("."),
    dataset_config_path=Path("training_inference/dataset_paths.config.json"),
)
```
