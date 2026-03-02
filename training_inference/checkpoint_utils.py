from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

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


def validate_checkpoint_smell_schema(
    checkpoint: Dict[str, Any],
    expected_smell_to_head: Mapping[str, int],
) -> None:
    """Fail fast when checkpoint smell routing schema does not match runtime expectations."""
    checkpoint_smell_to_head = checkpoint.get("smell_to_head")
    if not isinstance(checkpoint_smell_to_head, dict):
        raise ValueError("Checkpoint is missing a valid smell_to_head mapping.")

    checkpoint_map = {str(k): int(v) for k, v in checkpoint_smell_to_head.items()}
    expected_map = {str(k): int(v) for k, v in expected_smell_to_head.items()}

    if checkpoint_map == expected_map:
        return

    checkpoint_keys = set(checkpoint_map.keys())
    expected_keys = set(expected_map.keys())
    missing_in_checkpoint = sorted(expected_keys - checkpoint_keys)
    extra_in_checkpoint = sorted(checkpoint_keys - expected_keys)
    id_mismatches = sorted(
        key for key in (checkpoint_keys & expected_keys) if checkpoint_map[key] != expected_map[key]
    )

    parts = []
    if missing_in_checkpoint:
        parts.append("missing smells in checkpoint: " + ", ".join(missing_in_checkpoint))
    if extra_in_checkpoint:
        parts.append("extra smells in checkpoint: " + ", ".join(extra_in_checkpoint))
    if id_mismatches:
        preview = ", ".join(
            f"{key} (ckpt={checkpoint_map[key]}, expected={expected_map[key]})"
            for key in id_mismatches[:10]
        )
        if len(id_mismatches) > 10:
            preview += ", ..."
        parts.append("head id mismatches: " + preview)

    raise ValueError("Checkpoint smell schema mismatch: " + "; ".join(parts))
