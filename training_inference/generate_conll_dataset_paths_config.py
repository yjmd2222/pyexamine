from __future__ import annotations

import argparse
import json
from pathlib import Path

from training_inference.conll_data_utils import generate_conll_dataset_paths_config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a CoNLL dataset-path config JSON for training/inference."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Pyexamine repo root.",
    )
    parser.add_argument(
        "--dataset-root-dir",
        default="cdatasets",
        help="CoNLL dataset root directory under repo root (e.g., cdatasets).",
    )
    parser.add_argument(
        "--conll-name",
        default="role_section_excerpts.line.conll",
        help="Strict CoNLL filename required in each dataset directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("training_inference/conll_dataset_paths.config.json"),
        help="Output config JSON path.",
    )
    args = parser.parse_args()

    payload = generate_conll_dataset_paths_config(
        repo_root=args.repo_root,
        output_path=args.output,
        dataset_root_dir=args.dataset_root_dir,
        conll_name=args.conll_name,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
