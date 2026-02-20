from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn


@dataclass
class ModelOutputs:
    type_logits: torch.Tensor  # (B, N, num_types)
    mention_role_logits: torch.Tensor  # (B, N, K, num_roles)
    mention_start_logits: torch.Tensor  # (B, N, K, L)
    mention_end_logits: torch.Tensor  # (B, N, K, L)


class SpnSetPredictionModel(nn.Module):
    """SPN-style set prediction model for PyExamine DETR datasets.

    - Encoder: any HF encoder (AutoModel) that returns last_hidden_state.
    - Decoder: non-causal TransformerDecoder over N learnable Evidence queries.
    - Mentions: K mention slots per Evidence, created by adding learned mention-slot embeddings.

    The model predicts a set of smell Evidences. Each Evidence predicts:
      - smell type (including NO_OBJECT)
      - K mentions: role + start + end (including NO_MENTION)
    """

    def __init__(
        self,
        encoder,
        hidden_dim: int,
        num_types: int,
        num_roles: int,
        num_Evidence_queries: int,
        num_mention_slots: int,
        decoder_layers: int = 6,
        decoder_heads: int = 8,
        decoder_ffn_dim: int = 1024,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.encoder = encoder

        enc_dim = getattr(encoder.config, "hidden_size", None) or getattr(encoder.config, "d_model", None)
        if enc_dim is None:
            raise ValueError("Encoder config must expose hidden_size or d_model")

        self.enc_to_hidden = nn.Linear(enc_dim, hidden_dim)
        self.hidden_dim = hidden_dim

        # Learnable Evidence queries (N, D)
        self.Evidence_queries = nn.Embedding(num_Evidence_queries, hidden_dim)

        # Transformer decoder (non-causal)
        layer = nn.TransformerDecoderLayer(
            d_model=hidden_dim,
            nhead=decoder_heads,
            dim_feedforward=decoder_ffn_dim,
            dropout=dropout,
            batch_first=True,
        )
        self.decoder = nn.TransformerDecoder(layer, num_layers=decoder_layers)

        # Mention slot embeddings (K, D)
        self.mention_slot = nn.Embedding(num_mention_slots, hidden_dim)
        self.mention_mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        # Heads
        self.type_head = nn.Linear(hidden_dim, num_types)
        self.role_head = nn.Linear(hidden_dim, num_roles)

        # Pointer-style projections for start/end
        self.ptr_q_start = nn.Linear(hidden_dim, hidden_dim)
        self.ptr_q_end = nn.Linear(hidden_dim, hidden_dim)
        self.ptr_k = nn.Linear(hidden_dim, hidden_dim)

        self.dropout = nn.Dropout(dropout)

    def _pointer_logits(
        self,
        q: torch.Tensor,
        memory: torch.Tensor,
        memory_mask: Optional[torch.Tensor],
        q_proj: nn.Linear,
    ) -> torch.Tensor:
        """Compute dot-product pointer logits.

        Args:
            q: (B, Q, D)
            memory: (B, L, D)
            memory_mask: (B, L) where 1 indicates valid tokens.
            q_proj: projection layer for start/end queries (separate weights).
        Returns:
            logits: (B, Q, L)
        """
        qh = q_proj(q)  # (B,Q,D)
        kh = self.ptr_k(memory)  # (B,L,D)
        logits = torch.matmul(qh, kh.transpose(1, 2)) / (self.hidden_dim ** 0.5)
        if memory_mask is not None:
            # mask: 1 for valid, 0 for pad
            mask = (memory_mask == 0).unsqueeze(1)  # (B,1,L)
            logits = logits.masked_fill(mask, float("-inf"))
        return logits

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> ModelOutputs:
        # Encode
        enc = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        memory = enc.last_hidden_state
        memory = self.enc_to_hidden(memory)
        memory = self.dropout(memory)

        # Decode Evidence queries
        B = input_ids.size(0)
        N = self.Evidence_queries.num_embeddings
        inst_q = self.Evidence_queries.weight.unsqueeze(0).expand(B, N, -1)
        inst_h = self.decoder(tgt=inst_q, memory=memory, memory_key_padding_mask=(attention_mask == 0))
        inst_h = self.dropout(inst_h)

        type_logits = self.type_head(inst_h)

        # Mention embeddings: (B, N, K, D)
        K = self.mention_slot.num_embeddings
        slot = self.mention_slot.weight.unsqueeze(0).unsqueeze(0).expand(B, N, K, -1)
        mention_h = self.mention_mlp(inst_h).unsqueeze(2) + slot
        mention_h = self.dropout(mention_h)

        mention_role_logits = self.role_head(mention_h)  # (B,N,K,R)

        # Pointer logits: flatten mention queries to compute efficiently
        mention_flat = mention_h.reshape(B, N * K, -1)
        start_logits = self._pointer_logits(mention_flat, memory, attention_mask, self.ptr_q_start)
        end_logits = self._pointer_logits(mention_flat, memory, attention_mask, self.ptr_q_end)
        L = start_logits.size(-1)
        mention_start_logits = start_logits.view(B, N, K, L)
        mention_end_logits = end_logits.view(B, N, K, L)

        return ModelOutputs(
            type_logits=type_logits,
            mention_role_logits=mention_role_logits,
            mention_start_logits=mention_start_logits,
            mention_end_logits=mention_end_logits,
        )

