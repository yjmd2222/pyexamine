from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

import torch
import torch.nn as nn


@dataclass
class RoutedBatchOutput:
    """Container for model outputs.

    routed_logits: [B, T, C] logits for the smell head selected per sample.
    all_logits: Optional [B, S, T, C] for debugging/all-head inference.
    """

    routed_logits: torch.Tensor
    all_logits: Optional[torch.Tensor] = None
    hidden_states: Optional[torch.Tensor] = None


class SharedEncoderSmellHeads(nn.Module):
    """Shared encoder + smell-specific token classification heads.

    The backbone is any Hugging Face encoder that returns `last_hidden_state` with shape [B, T, H].
    Each smell has its own token classification head that predicts the same BIO label space.

    Notes
    -----
    - Training is *routed*: only the head corresponding to each sample's `smell_name`
      is supervised. This avoids accidental negative supervision on the other 45 heads.
    - Inference can return routed logits only (fast) or all-head logits (debugging).
    """

    def __init__(
        self,
        backbone: nn.Module,
        hidden_size: int,
        num_smells: int,
        num_labels: int,
        dropout: float = 0.1,
        use_shared_proj: bool = True,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        self.hidden_size = int(hidden_size)
        self.num_smells = int(num_smells)
        self.num_labels = int(num_labels)
        self.dropout = nn.Dropout(dropout)
        self.shared_proj = (
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.GELU(),
                nn.Dropout(dropout),
            )
            if use_shared_proj
            else nn.Identity()
        )
        self.heads = nn.ModuleList([nn.Linear(hidden_size, num_labels) for _ in range(num_smells)])

    @classmethod
    def from_hf_pretrained(
        cls,
        backbone_name: str,
        num_smells: int,
        num_labels: int,
        dropout: float = 0.1,
        use_shared_proj: bool = True,
        trust_remote_code: bool = False,
        **model_kwargs,
    ) -> "SharedEncoderSmellHeads":
        """Create model from a Hugging Face checkpoint (e.g., ModernBERT).

        We keep the import inside the method so the repo remains importable even when
        `transformers` isn't installed yet.
        """
        try:
            from transformers import AutoModel
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError(
                "transformers is required to instantiate the ModernBERT backbone. "
                "Install with: pip install transformers"
            ) from exc

        backbone = AutoModel.from_pretrained(
            backbone_name,
            trust_remote_code=trust_remote_code,
            **model_kwargs,
        )
        hidden_size = getattr(backbone.config, "hidden_size", None)
        if hidden_size is None:
            raise ValueError("Backbone config does not expose `hidden_size`.")
        return cls(
            backbone=backbone,
            hidden_size=hidden_size,
            num_smells=num_smells,
            num_labels=num_labels,
            dropout=dropout,
            use_shared_proj=use_shared_proj,
        )

    def encode(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
        **backbone_kwargs,
    ) -> torch.Tensor:
        kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            **backbone_kwargs,
        }
        if token_type_ids is not None:
            kwargs["token_type_ids"] = token_type_ids

        out = self.backbone(**kwargs)
        if hasattr(out, "last_hidden_state"):
            hidden = out.last_hidden_state
        elif isinstance(out, (tuple, list)):
            hidden = out[0]
        else:
            hidden = out

        hidden = self.dropout(hidden)
        hidden = self.shared_proj(hidden)
        return hidden

    def forward_all_heads(self, hidden: torch.Tensor, head_ids: Optional[Sequence[int]] = None) -> torch.Tensor:
        if head_ids is None:
            selected = self.heads
        else:
            selected = [self.heads[i] for i in head_ids]
        return torch.stack([head(hidden) for head in selected], dim=1)  # [B, S, T, C]

    def forward_routed(
        self,
        hidden: torch.Tensor,
        routed_head_ids: torch.Tensor,
    ) -> torch.Tensor:
        """Compute only routed logits per sample.

        Parameters
        ----------
        hidden: [B, T, H]
        routed_head_ids: [B] long tensor with smell-head index for each sample
        """
        if routed_head_ids.dim() != 1 or routed_head_ids.size(0) != hidden.size(0):
            raise ValueError("routed_head_ids must have shape [B].")

        B, T, _ = hidden.shape
        device = hidden.device
        routed_logits = torch.empty(
            (B, T, self.num_labels),
            device=device,
            dtype=hidden.dtype,
        )

        unique_heads = routed_head_ids.unique(sorted=True)
        for head_idx_tensor in unique_heads:
            head_idx = int(head_idx_tensor.item())
            sample_mask = routed_head_ids == head_idx_tensor
            routed_logits[sample_mask] = self.heads[head_idx](hidden[sample_mask])
        return routed_logits

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        routed_head_ids: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
        return_all_heads: bool = False,
        return_hidden_states: bool = False,
        **backbone_kwargs,
    ) -> RoutedBatchOutput:
        hidden = self.encode(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            **backbone_kwargs,
        )

        all_logits = None
        if routed_head_ids is None:
            # If no routing provided, default to all-head mode and use head 0 for routed placeholder.
            all_logits = self.forward_all_heads(hidden)
            routed_logits = all_logits[:, 0]
        else:
            routed_logits = self.forward_routed(hidden, routed_head_ids=routed_head_ids)
            if return_all_heads:
                all_logits = self.forward_all_heads(hidden)

        return RoutedBatchOutput(
            routed_logits=routed_logits,
            all_logits=all_logits,
            hidden_states=hidden if return_hidden_states else None,
        )


def compute_token_ce_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    ignore_index: int = -100,
    class_weights: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """CrossEntropyLoss for routed token logits.

    logits: [B, T, C]
    labels: [B, T]
    """
    if logits.ndim != 3:
        raise ValueError(f"Expected logits [B,T,C], got {tuple(logits.shape)}")
    if labels.shape != logits.shape[:2]:
        raise ValueError(
            f"Label shape {tuple(labels.shape)} must match logits[:2] {tuple(logits.shape[:2])}"
        )

    B, T, C = logits.shape
    flat_logits = logits.reshape(B * T, C)
    flat_labels = labels.reshape(B * T)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights, ignore_index=ignore_index)
    return loss_fn(flat_logits, flat_labels)


def build_optimizer(
    model: nn.Module,
    lr: float = 2e-5,
    weight_decay: float = 0.01,
    betas: Sequence[float] = (0.9, 0.999),
) -> torch.optim.Optimizer:
    """Reasonable default AdamW setup for backbone fine-tuning."""
    return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay, betas=tuple(betas))


def freeze_backbone(model: SharedEncoderSmellHeads, freeze: bool = True) -> None:
    for p in model.backbone.parameters():
        p.requires_grad = not freeze


def unfreeze_top_n_backbone_layers(model: SharedEncoderSmellHeads, n_layers: int) -> None:
    """Best-effort helper for partial fine-tuning.

    Different HF backbones expose layers under different attribute names. This helper tries
    common layouts and otherwise falls back to full unfreeze.
    """
    freeze_backbone(model, True)
    layer_containers: List[Iterable[nn.Module]] = []

    for path in [
        ["encoder", "layer"],
        ["bert", "encoder", "layer"],
        ["model", "layers"],
        ["layers"],
    ]:
        obj = model.backbone
        ok = True
        for attr in path:
            if hasattr(obj, attr):
                obj = getattr(obj, attr)
            else:
                ok = False
                break
        if ok and isinstance(obj, (list, nn.ModuleList)):
            layer_containers.append(obj)
            break

    if not layer_containers:
        # Fallback: full unfreeze when the layout is unknown.
        freeze_backbone(model, False)
        return

    layers = list(layer_containers[0])
    for layer in layers[-int(n_layers):]:
        for p in layer.parameters():
            p.requires_grad = True

    # Keep embeddings trainable only if all layers are requested.
    if n_layers >= len(layers):
        for p in model.backbone.parameters():
            p.requires_grad = True
