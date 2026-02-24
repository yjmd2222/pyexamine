from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import torch
from torch.utils.data import DataLoader

from .train_loop import _move_batch_to_device


@torch.no_grad()
def run_batched_inference(
    model,
    dataloader: DataLoader,
    device: torch.device,
    id_to_label: Dict[int, str],
    routed_only: bool = True,
    return_probabilities: bool = False,
    probability_topk: Optional[int] = None,
    amp_enabled: bool = False,
) -> List[Dict[str, Any]]:
    """Run batched token classification inference.

    Output format is JSONL-friendly and includes `id` for later sidecar join.
    NOTE: sidecar integration is intentionally deferred (placeholder below), per user request.
    """
    model.eval()
    model.to(device)
    outputs: List[Dict[str, Any]] = []

    for batch in dataloader:
        batch_device = _move_batch_to_device(batch, device)

        autocast_enabled = amp_enabled and device.type == "cuda"
        with torch.autocast(device_type=device.type, enabled=autocast_enabled):
            model_out = model(
                input_ids=batch_device["input_ids"],
                attention_mask=batch_device["attention_mask"],
                routed_head_ids=batch_device["smell_head_ids"],
                return_all_heads=not routed_only,
            )

        routed_logits = model_out.routed_logits
        routed_pred_ids = routed_logits.argmax(dim=-1)

        routed_probs = None
        if return_probabilities:
            routed_probs = torch.softmax(routed_logits.float(), dim=-1)

        for i in range(routed_logits.size(0)):
            seq_len = int(batch_device["attention_mask"][i].sum().item())
            pred_ids = routed_pred_ids[i, :seq_len].detach().cpu().tolist()
            pred_labels = [id_to_label[int(x)] for x in pred_ids]

            rec: Dict[str, Any] = {
                "id": batch["ids"][i],
                "smell_name": batch["smell_names"][i],
                "is_detected": batch["is_detected"][i],
                "was_truncated": bool(batch["was_truncated"][i]),
                "pred_label_ids": pred_ids,
                "pred_labels": pred_labels,
            }

            if return_probabilities and routed_probs is not None:
                probs_seq = routed_probs[i, :seq_len].detach().cpu()
                if probability_topk is None:
                    rec["pred_token_probs"] = probs_seq.tolist()
                else:
                    k = int(probability_topk)
                    top_probs, top_ids = probs_seq.topk(k=min(k, probs_seq.size(-1)), dim=-1)
                    rec["pred_token_topk"] = [
                        [
                            {"label_id": int(li), "label": id_to_label[int(li)], "prob": float(lp)}
                            for lp, li in zip(prob_row.tolist(), id_row.tolist())
                        ]
                        for prob_row, id_row in zip(top_probs, top_ids)
                    ]

            if not routed_only and model_out.all_logits is not None:
                # Optional debugging: return argmax for all heads (can be large). Keep compact by default.
                all_logits = model_out.all_logits[i, :, :seq_len].detach().cpu()
                rec["all_heads_pred_label_ids"] = all_logits.argmax(dim=-1).tolist()

            # Placeholder: join with `role_section_excerpts.sidecar.jsonl` later by `id`.
            # We intentionally do not read sidecar here (user requested training/inference without sidecar for now).
            outputs.append(rec)

    return outputs


def save_inference_outputs_jsonl(records: Sequence[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def preview_inference_records(records: Sequence[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
    return list(records[:n])
