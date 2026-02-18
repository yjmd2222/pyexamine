# SPN-style training (encoder + non-causal query decoder + Hungarian matching)

This repo can generate DETR-format datasets via:

```bash
python -m pyexamine smell_dataset <code_root> --config <cfg.yaml> --report <report.json> --output-dir <outdir> --format detr
```

The DETR dataset file lives at:

```
<outdir>/detr_dataset.json
```

## Install ML dependencies

```bash
pip install -e .[ml]
```

## Train

Edit `configs/spn_train.yaml` and set `data.dataset_root` to the directory that contains your `datasets/*/detr_dataset.json`.

Then run:

```bash
python -m spn_training --config configs/spn_train.yaml
```

Checkpoints and vocab files will be written under `train.output_dir`.

## Notes

- The training pipeline uses token windows (`max_length`, `stride`).
- A gold smell instance is included in a window only if **all its mention spans** fall fully inside that window.


## Python 3.12 + CUDA notes

- Recommended (tested) versions for Python 3.12:
  - torch >= 2.2
  - transformers >= 4.38
  - scipy >= 1.11.4
  - numpy >= 1.26.4

- Install PyTorch with the CUDA build that matches your driver/toolkit (use the official PyTorch install selector).
- In `configs/spn_train.yaml`, set `train.device: auto` (default) to use CUDA when available.
