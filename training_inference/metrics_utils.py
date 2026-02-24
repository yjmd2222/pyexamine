from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import torch

IGNORE_INDEX = -100


@dataclass
class TokenEvalBundle:
    loss: Optional[float]
    metrics: Dict[str, float]
    per_label: Dict[str, Dict[str, float]]
    seqeval: Optional[Dict[str, float]]


def flatten_valid_tokens(
    preds: torch.Tensor,
    labels: torch.Tensor,
    ignore_index: int = IGNORE_INDEX,
) -> Tuple[List[int], List[int]]:
    """Flatten [B,T] predictions/labels while removing ignored labels."""
    if preds.shape != labels.shape:
        raise ValueError(f"preds and labels must have same shape. got {preds.shape} vs {labels.shape}")
    mask = labels != ignore_index
    flat_preds = preds[mask].detach().cpu().tolist()
    flat_labels = labels[mask].detach().cpu().tolist()
    return flat_preds, flat_labels


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def compute_token_metrics_from_flat_ids(
    flat_preds: Sequence[int],
    flat_labels: Sequence[int],
    id_to_label: Dict[int, str],
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """Token-level metrics (micro + per-label) over non-ignored tokens.

    We report token accuracy and micro precision/recall/F1. Since this is single-label
    token classification, micro precision == micro recall == micro F1 == accuracy across
    the included labels, but we keep the fields for readability.
    """
    if len(flat_preds) != len(flat_labels):
        raise ValueError("Prediction/label lengths differ")

    total = len(flat_labels)
    correct = sum(int(p == y) for p, y in zip(flat_preds, flat_labels))

    label_ids = sorted(set(flat_labels) | set(flat_preds))
    per_label: Dict[str, Dict[str, float]] = {}

    # Confusion counts per class for one-vs-rest summaries.
    for lid in label_ids:
        tp = sum(int(p == lid and y == lid) for p, y in zip(flat_preds, flat_labels))
        fp = sum(int(p == lid and y != lid) for p, y in zip(flat_preds, flat_labels))
        fn = sum(int(p != lid and y == lid) for p, y in zip(flat_preds, flat_labels))
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
        support = sum(int(y == lid) for y in flat_labels)
        per_label[id_to_label.get(lid, str(lid))] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": float(support),
        }

    accuracy = _safe_div(correct, total)

    # Micro stats over all classes in single-label setting.
    micro_tp = correct
    micro_fp = total - correct
    micro_fn = total - correct
    micro_precision = _safe_div(micro_tp, micro_tp + micro_fp)
    micro_recall = _safe_div(micro_tp, micro_tp + micro_fn)
    micro_f1 = _safe_div(2 * micro_precision * micro_recall, micro_precision + micro_recall) if (micro_precision + micro_recall) else 0.0

    # Often `O` dominates token classification. Provide an O-excluded micro F1 too.
    o_label = "O"
    o_id = None
    for i, name in id_to_label.items():
        if name == o_label:
            o_id = i
            break
    if o_id is not None:
        mask_non_o = [y != o_id for y in flat_labels]
        non_o_pairs = [(p, y) for (p, y), keep in zip(zip(flat_preds, flat_labels), mask_non_o) if keep]
        if non_o_pairs:
            no_total = len(non_o_pairs)
            no_correct = sum(int(p == y) for p, y in non_o_pairs)
            non_o_micro_f1 = _safe_div(no_correct, no_total)  # same as micro in single-label setting
        else:
            non_o_micro_f1 = 0.0
    else:
        non_o_micro_f1 = 0.0

    metrics = {
        "token_accuracy": accuracy,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "non_o_micro_f1": non_o_micro_f1,
        "num_valid_tokens": float(total),
    }
    return metrics, per_label


def ids_to_label_sequences(
    preds: torch.Tensor,
    labels: torch.Tensor,
    id_to_label: Dict[int, str],
    ignore_index: int = IGNORE_INDEX,
) -> Tuple[List[List[str]], List[List[str]]]:
    """Convert [B,T] ids into seqeval-ready sequences, dropping ignored positions."""
    if preds.shape != labels.shape:
        raise ValueError("preds and labels must match")
    pred_seqs: List[List[str]] = []
    gold_seqs: List[List[str]] = []
    preds_cpu = preds.detach().cpu()
    labels_cpu = labels.detach().cpu()
    for p_row, y_row in zip(preds_cpu, labels_cpu):
        pred_seq: List[str] = []
        gold_seq: List[str] = []
        for p, y in zip(p_row.tolist(), y_row.tolist()):
            if y == ignore_index:
                continue
            pred_seq.append(id_to_label[int(p)])
            gold_seq.append(id_to_label[int(y)])
        pred_seqs.append(pred_seq)
        gold_seqs.append(gold_seq)
    return pred_seqs, gold_seqs


def compute_seqeval_metrics(pred_seqs: Sequence[Sequence[str]], gold_seqs: Sequence[Sequence[str]]) -> Optional[Dict[str, float]]:
    """Entity/span-level BIO metrics via seqeval (optional dependency)."""
    try:
        from seqeval.metrics import f1_score, precision_score, recall_score, accuracy_score
    except ImportError:
        return None

    return {
        "seqeval_precision": float(precision_score(gold_seqs, pred_seqs)),
        "seqeval_recall": float(recall_score(gold_seqs, pred_seqs)),
        "seqeval_f1": float(f1_score(gold_seqs, pred_seqs)),
        "seqeval_accuracy": float(accuracy_score(gold_seqs, pred_seqs)),
    }


def compute_token_eval_bundle(
    preds: torch.Tensor,
    labels: torch.Tensor,
    id_to_label: Dict[int, str],
    loss: Optional[float] = None,
    ignore_index: int = IGNORE_INDEX,
) -> TokenEvalBundle:
    flat_preds, flat_labels = flatten_valid_tokens(preds=preds, labels=labels, ignore_index=ignore_index)
    metrics, per_label = compute_token_metrics_from_flat_ids(flat_preds, flat_labels, id_to_label=id_to_label)
    pred_seqs, gold_seqs = ids_to_label_sequences(preds=preds, labels=labels, id_to_label=id_to_label, ignore_index=ignore_index)
    seqeval_metrics = compute_seqeval_metrics(pred_seqs, gold_seqs)
    return TokenEvalBundle(loss=loss, metrics=metrics, per_label=per_label, seqeval=seqeval_metrics)


def pretty_print_metrics(bundle: TokenEvalBundle) -> None:
    if bundle.loss is not None:
        print(f"loss: {bundle.loss:.6f}")
    for k, v in sorted(bundle.metrics.items()):
        print(f"{k}: {v:.6f}")
    if bundle.seqeval is None:
        print("seqeval: not available (install seqeval for span/entity BIO metrics)")
    else:
        for k, v in sorted(bundle.seqeval.items()):
            print(f"{k}: {v:.6f}")
