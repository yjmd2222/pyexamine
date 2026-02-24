from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import torch
from torch.utils.data import DataLoader

from .metrics_utils import (
    compute_seqeval_metrics,
    compute_token_metrics_from_flat_ids,
    flatten_valid_tokens,
    ids_to_label_sequences,
)
from .model_pipeline import compute_token_ce_loss


@dataclass
class EpochResult:
    epoch: int
    train_loss: float
    val_loss: float
    val_metrics: Dict[str, float]
    val_seqeval: Optional[Dict[str, float]]


@dataclass
class TrainingArtifacts:
    history: List[EpochResult]
    best_checkpoint_path: Optional[str]
    last_checkpoint_path: Optional[str]


def set_global_seed(seed: int = 42, deterministic: bool = True) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        # This can make some ops slower, but the user explicitly requested deterministic reproducibility.
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def _move_batch_to_device(batch: Dict[str, Any], device: torch.device) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in batch.items():
        if torch.is_tensor(v):
            out[k] = v.to(device)
        else:
            out[k] = v
    return out


def make_dataloader(
    dataset,
    collator,
    batch_size: int,
    shuffle: bool,
    num_workers: int = 0,
    pin_memory: bool = True,
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        collate_fn=collator,
    )


def _amp_context(device: torch.device, enabled: bool):
    if not enabled:
        return torch.autocast(device_type=device.type, enabled=False)
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    # CPU autocast is not always beneficial and depends on PyTorch build. Disable by default on CPU.
    return torch.autocast(device_type=device.type, enabled=False)


@torch.no_grad()
def evaluate_model(
    model,
    dataloader: DataLoader,
    device: torch.device,
    id_to_label: Dict[int, str],
    class_weights: Optional[torch.Tensor] = None,
    amp_enabled: bool = False,
    max_batches: Optional[int] = None,
) -> Dict[str, Any]:
    model.eval()
    total_loss = 0.0
    total_batches = 0
    flat_preds_all: List[int] = []
    flat_labels_all: List[int] = []
    pred_seqs_all: List[List[str]] = []
    gold_seqs_all: List[List[str]] = []
    trunc_count = 0
    total_examples = 0

    class_weights_dev = class_weights.to(device) if class_weights is not None else None

    for b_idx, batch in enumerate(dataloader):
        if max_batches is not None and b_idx >= max_batches:
            break
        total_examples += len(batch["ids"])
        trunc_count += sum(bool(x) for x in batch.get("was_truncated", []))
        batch = _move_batch_to_device(batch, device)

        with _amp_context(device, amp_enabled):
            out = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                routed_head_ids=batch["smell_head_ids"],
                return_all_heads=False,
            )
            loss = compute_token_ce_loss(
                logits=out.routed_logits,
                labels=batch["labels"],
                ignore_index=-100,
                class_weights=class_weights_dev,
            )
        total_loss += float(loss.item())
        total_batches += 1

        preds = out.routed_logits.argmax(dim=-1)
        labels_cpu = batch["labels"].detach().cpu()
        preds_cpu = preds.detach().cpu()

        flat_preds, flat_labels = flatten_valid_tokens(preds=preds_cpu, labels=labels_cpu, ignore_index=-100)
        flat_preds_all.extend(flat_preds)
        flat_labels_all.extend(flat_labels)

        pred_seqs, gold_seqs = ids_to_label_sequences(preds=preds_cpu, labels=labels_cpu, id_to_label=id_to_label, ignore_index=-100)
        pred_seqs_all.extend(pred_seqs)
        gold_seqs_all.extend(gold_seqs)

    if total_batches == 0:
        raise RuntimeError("No evaluation batches were processed.")

    avg_loss = total_loss / total_batches
    metrics, per_label = compute_token_metrics_from_flat_ids(flat_preds_all, flat_labels_all, id_to_label=id_to_label)
    seqeval = compute_seqeval_metrics(pred_seqs_all, gold_seqs_all)

    return {
        "loss": avg_loss,
        "metrics": metrics,
        "seqeval": seqeval,
        "per_label": per_label,
        "truncated_examples": trunc_count,
        "num_examples": total_examples,
    }


def _build_debug_preview_from_batch(batch: Dict[str, Any], pred_ids: torch.Tensor, id_to_label: Dict[int, str], n: int = 3) -> List[Dict[str, Any]]:
    previews: List[Dict[str, Any]] = []
    pred_ids_cpu = pred_ids.detach().cpu()
    label_ids_cpu = batch["labels"].detach().cpu()

    for i in range(min(n, len(batch["ids"]))):
        input_ids_len = int((batch["attention_mask"][i] == 1).sum().item())
        pred_labels = [id_to_label[int(x)] for x in pred_ids_cpu[i, :input_ids_len].tolist()]
        gold_labels = []
        for x in label_ids_cpu[i, :input_ids_len].tolist():
            gold_labels.append("-100" if x == -100 else id_to_label[int(x)])
        previews.append(
            {
                "id": batch["ids"][i],
                "smell_name": batch["smell_names"][i],
                "is_detected": batch["is_detected"][i],
                "was_truncated": batch["was_truncated"][i],
                "raw_tokens": batch["raw_tokens"][i],
                "gold_raw_labels": batch["raw_labels"][i],
                "gold_subword_labels": gold_labels,
                "pred_subword_labels": pred_labels,
                "word_ids": batch["word_ids"][i],
            }
        )
    return previews


def save_checkpoint(
    checkpoint_path: Path,
    model,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    global_step: int,
    tokenizer_name_or_path: str,
    label_to_id: Dict[str, int],
    smell_to_head: Dict[str, int],
    history: Sequence[EpochResult],
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "epoch": int(epoch),
        "global_step": int(global_step),
        "tokenizer_name_or_path": tokenizer_name_or_path,
        "label_to_id": dict(label_to_id),
        "smell_to_head": dict(smell_to_head),
        "history": [asdict(h) for h in history],
        "extra": extra or {},
    }
    torch.save(payload, checkpoint_path)


def load_checkpoint(checkpoint_path: Path, model, optimizer: Optional[torch.optim.Optimizer] = None, map_location: str = "cpu") -> Dict[str, Any]:
    ckpt = torch.load(checkpoint_path, map_location=map_location)
    model.load_state_dict(ckpt["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in ckpt:
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    return ckpt


def train_model(
    model,
    train_loader: DataLoader,
    val_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    id_to_label: Dict[int, str],
    label_to_id: Dict[str, int],
    smell_to_head: Dict[str, int],
    tokenizer_name_or_path: str,
    output_dir: Path,
    num_epochs: int = 3,
    grad_accum_steps: int = 1,
    max_grad_norm: Optional[float] = 1.0,
    amp_enabled: bool = True,
    class_weights: Optional[torch.Tensor] = None,
    save_every_epoch: bool = True,
    resume_checkpoint_path: Optional[Path] = None,
    debug_preview_count: int = 3,
) -> TrainingArtifacts:
    output_dir = Path(output_dir)
    ckpt_dir = output_dir / "checkpoints"
    preview_dir = output_dir / "debug_previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = model.to(device)
    scaler = torch.cuda.amp.GradScaler(enabled=(amp_enabled and device.type == "cuda"))

    history: List[EpochResult] = []
    best_checkpoint_path: Optional[str] = None
    last_checkpoint_path: Optional[str] = None
    best_val_f1 = -1.0
    start_epoch = 0
    global_step = 0

    if resume_checkpoint_path is not None:
        ckpt = load_checkpoint(resume_checkpoint_path, model=model, optimizer=optimizer, map_location=device.type)
        start_epoch = int(ckpt.get("epoch", 0)) + 1
        global_step = int(ckpt.get("global_step", 0))
        prev_hist = ckpt.get("history", [])
        for item in prev_hist:
            history.append(EpochResult(**item))

    class_weights_dev = class_weights.to(device) if class_weights is not None else None

    for epoch in range(start_epoch, num_epochs):
        model.train()
        running_loss = 0.0
        n_batches = 0
        trunc_count_train = 0
        total_train_examples = 0

        optimizer.zero_grad(set_to_none=True)
        first_debug_preview_saved = False

        for step, batch in enumerate(train_loader):
            total_train_examples += len(batch["ids"])
            trunc_count_train += sum(bool(x) for x in batch.get("was_truncated", []))
            batch = _move_batch_to_device(batch, device)

            with _amp_context(device, amp_enabled):
                out = model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    routed_head_ids=batch["smell_head_ids"],
                    return_all_heads=False,
                )
                loss = compute_token_ce_loss(
                    logits=out.routed_logits,
                    labels=batch["labels"],
                    ignore_index=-100,
                    class_weights=class_weights_dev,
                )
                loss = loss / grad_accum_steps

            if scaler.is_enabled():
                scaler.scale(loss).backward()
            else:
                loss.backward()

            if (step + 1) % grad_accum_steps == 0:
                if max_grad_norm is not None:
                    if scaler.is_enabled():
                        scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                if scaler.is_enabled():
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

            running_loss += float(loss.item()) * grad_accum_steps
            n_batches += 1

            if not first_debug_preview_saved:
                preds = out.routed_logits.argmax(dim=-1)
                previews = _build_debug_preview_from_batch(batch, preds, id_to_label=id_to_label, n=debug_preview_count)
                (preview_dir / f"epoch_{epoch:03d}_train_first_batch_preview.json").write_text(
                    json.dumps(previews, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                first_debug_preview_saved = True

        train_loss = running_loss / max(n_batches, 1)

        eval_out = evaluate_model(
            model=model,
            dataloader=val_loader,
            device=device,
            id_to_label=id_to_label,
            class_weights=class_weights_dev,
            amp_enabled=amp_enabled,
        )

        epoch_result = EpochResult(
            epoch=epoch,
            train_loss=float(train_loss),
            val_loss=float(eval_out["loss"]),
            val_metrics={k: float(v) for k, v in eval_out["metrics"].items()},
            val_seqeval={k: float(v) for k, v in eval_out["seqeval"].items()} if eval_out["seqeval"] else None,
        )
        history.append(epoch_result)

        # Persist a small metrics snapshot and truncation report each epoch.
        metrics_payload = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": eval_out["loss"],
            "val_metrics": eval_out["metrics"],
            "val_seqeval": eval_out["seqeval"],
            "train_truncated_examples": trunc_count_train,
            "train_num_examples": total_train_examples,
            "val_truncated_examples": int(eval_out["truncated_examples"]),
            "val_num_examples": int(eval_out["num_examples"]),
        }
        (output_dir / f"epoch_{epoch:03d}_metrics.json").write_text(
            json.dumps(metrics_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if save_every_epoch:
            epoch_ckpt = ckpt_dir / f"epoch_{epoch:03d}.pt"
            save_checkpoint(
                checkpoint_path=epoch_ckpt,
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                global_step=global_step,
                tokenizer_name_or_path=tokenizer_name_or_path,
                label_to_id=label_to_id,
                smell_to_head=smell_to_head,
                history=history,
                extra={
                    "train_truncated_examples": trunc_count_train,
                    "val_truncated_examples": eval_out["truncated_examples"],
                },
            )
            last_checkpoint_path = str(epoch_ckpt)

        val_f1 = eval_out["seqeval"]["seqeval_f1"] if eval_out["seqeval"] and "seqeval_f1" in eval_out["seqeval"] else eval_out["metrics"].get("non_o_micro_f1", 0.0)
        if val_f1 > best_val_f1:
            best_val_f1 = float(val_f1)
            best_ckpt = ckpt_dir / "best.pt"
            save_checkpoint(
                checkpoint_path=best_ckpt,
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                global_step=global_step,
                tokenizer_name_or_path=tokenizer_name_or_path,
                label_to_id=label_to_id,
                smell_to_head=smell_to_head,
                history=history,
                extra={
                    "selected_metric": "seqeval_f1" if (eval_out["seqeval"] and "seqeval_f1" in eval_out["seqeval"]) else "non_o_micro_f1",
                    "selected_metric_value": best_val_f1,
                },
            )
            best_checkpoint_path = str(best_ckpt)

        # Console-friendly summary for notebooks.
        print(
            f"[epoch {epoch}] train_loss={train_loss:.4f} val_loss={eval_out['loss']:.4f} "
            f"micro_f1={eval_out['metrics'].get('micro_f1', 0.0):.4f} "
            f"non_o_micro_f1={eval_out['metrics'].get('non_o_micro_f1', 0.0):.4f} "
            f"seqeval_f1={(eval_out['seqeval'] or {}).get('seqeval_f1', float('nan')):.4f}"
        )
        print(
            f"  truncation report: train {trunc_count_train}/{total_train_examples}, "
            f"val {eval_out['truncated_examples']}/{eval_out['num_examples']}"
        )

    # Save a lightweight history json for notebook plotting/reporting.
    (output_dir / "history.json").write_text(
        json.dumps([asdict(h) for h in history], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return TrainingArtifacts(
        history=history,
        best_checkpoint_path=best_checkpoint_path,
        last_checkpoint_path=last_checkpoint_path,
    )
