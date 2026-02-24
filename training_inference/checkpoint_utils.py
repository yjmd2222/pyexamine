from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import torch

from .model_pipeline import SharedEncoderSmellHeads


def load_training_checkpoint(checkpoint_path: Path, map_location: str = "cpu") -> Dict[str, Any]:
    return torch.load(Path(checkpoint_path), map_location=map_location)


def build_model_from_checkpoint_metadata(
    checkpoint: Dict[str, Any],
    backbone_name: Optional[str] = None,
    trust_remote_code: bool = False,
    **model_kwargs,
) -> SharedEncoderSmellHeads:
    tokenizer_name_or_path = checkpoint.get("tokenizer_name_or_path")
    backbone_name = backbone_name or tokenizer_name_or_path
    if not backbone_name:
        raise ValueError("Checkpoint does not contain tokenizer/backbone name, and no override was provided.")

    label_to_id = checkpoint["label_to_id"]
    smell_to_head = checkpoint["smell_to_head"]
    model = SharedEncoderSmellHeads.from_hf_pretrained(
        backbone_name=str(backbone_name),
        num_smells=len(smell_to_head),
        num_labels=len(label_to_id),
        trust_remote_code=trust_remote_code,
        **model_kwargs,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    return model
