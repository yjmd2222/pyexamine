from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import yaml


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    # Avoid crashing on CPU-only builds of PyTorch.
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _device_from_cfg(s: str) -> torch.device:
    if s == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(s)


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _split_train_val(paths: List[str], val_ratio: float) -> Tuple[List[str], List[str]]:
    # Deterministic split by sample_id (directory name).
    sample_ids = sorted({os.path.basename(os.path.dirname(p)) for p in paths})
    n_val = max(1, int(round(len(sample_ids) * val_ratio))) if len(sample_ids) > 1 else 0
    val_ids = set(sample_ids[-n_val:])
    train = [p for p in paths if os.path.basename(os.path.dirname(p)) not in val_ids]
    val = [p for p in paths if os.path.basename(os.path.dirname(p)) in val_ids]
    return train, val


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an SPN-style set prediction model on PyExamine DETR datasets.")
    parser.add_argument("--config", required=True, help="Path to configs/spn_train.yaml")
    args = parser.parse_args()

    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))

    seed = int(cfg.get("seed", 42))
    set_seed(seed)

    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    loss_cfg = cfg["loss"]
    train_cfg = cfg["train"]

    device = _device_from_cfg(train_cfg.get("device", "auto"))
    out_dir = train_cfg["output_dir"]
    _ensure_dir(out_dir)

    # Lazy imports: keep repo usable without ML deps unless training is invoked.
    from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

    from .datasets import (
        build_label_vocab,
        collate_window_examples,
        iter_window_examples,
        list_detr_jsons,
    )
    from .losses import LossConfig, compute_set_loss
    from .model import SpnSetPredictionModel

    detr_paths = list_detr_jsons(data_cfg["dataset_root"], data_cfg["detr_glob"])
    if not detr_paths:
        raise SystemExit(f"No detr_dataset.json found under {data_cfg['dataset_root']} with glob {data_cfg['detr_glob']}")

    train_paths, val_paths = _split_train_val(detr_paths, float(data_cfg.get("val_ratio", 0.2)))

    smell2id, role2id = build_label_vocab(detr_paths)
    # Persist vocab for reproducibility
    json.dump(smell2id, open(os.path.join(out_dir, "smell2id.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(role2id, open(os.path.join(out_dir, "role2id.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    tokenizer = AutoTokenizer.from_pretrained(model_cfg["encoder_name"], use_fast=True)
    encoder = AutoModel.from_pretrained(model_cfg["encoder_name"])

    freeze_encoder = bool(model_cfg.get("freeze_encoder", False))
    if freeze_encoder:
        for p in encoder.parameters():
            p.requires_grad = False

    model = SpnSetPredictionModel(
        encoder=encoder,
        hidden_dim=int(model_cfg["hidden_dim"]),
        num_types=len(smell2id),
        num_roles=len(role2id),
        num_Evidence_queries=int(data_cfg.get("max_Evidences_per_window", 100)),
        num_mention_slots=int(data_cfg.get("max_mentions_per_Evidence", 16)),
        decoder_layers=int(model_cfg.get("decoder_layers", 6)),
        decoder_heads=int(model_cfg.get("decoder_heads", 8)),
        decoder_ffn_dim=int(model_cfg.get("decoder_ffn_dim", 1024)),
        dropout=float(model_cfg.get("dropout", 0.1)),
    ).to(device)

    # Datasets (materialize window examples once; dataset is small)
    train_examples = list(
        iter_window_examples(
            detr_paths=train_paths,
            tokenizer=tokenizer,
            smell2id=smell2id,
            role2id=role2id,
            max_length=int(data_cfg["max_length"]),
            stride=int(data_cfg["stride"]),
            max_Evidences=int(data_cfg.get("max_Evidences_per_window", 100)),
            max_mentions=int(data_cfg.get("max_mentions_per_Evidence", 16)),
            drop_empty_windows=bool(data_cfg.get("drop_empty_windows", True)),
        )
    )
    val_examples = list(
        iter_window_examples(
            detr_paths=val_paths,
            tokenizer=tokenizer,
            smell2id=smell2id,
            role2id=role2id,
            max_length=int(data_cfg["max_length"]),
            stride=int(data_cfg["stride"]),
            max_Evidences=int(data_cfg.get("max_Evidences_per_window", 100)),
            max_mentions=int(data_cfg.get("max_mentions_per_Evidence", 16)),
            drop_empty_windows=bool(data_cfg.get("drop_empty_windows", True)),
        )
    )

    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    train_loader = DataLoader(
        train_examples,
        batch_size=int(train_cfg["batch_size"]),
        shuffle=True,
        collate_fn=lambda b: collate_window_examples(b, pad_id),
    )
    val_loader = DataLoader(
        val_examples,
        batch_size=int(train_cfg["batch_size"]),
        shuffle=False,
        collate_fn=lambda b: collate_window_examples(b, pad_id),
    )

    # Optimizer + schedule
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(trainable_params, lr=float(train_cfg["lr"]), weight_decay=float(train_cfg["weight_decay"]))
    total_steps = int(train_cfg["epochs"]) * max(1, len(train_loader))
    warmup_steps = int(total_steps * float(train_cfg.get("warmup_ratio", 0.06)))
    sched = get_linear_schedule_with_warmup(opt, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    loss_conf = LossConfig(
        type_weight=float(loss_cfg.get("type_weight", 1.0)),
        mention_role_weight=float(loss_cfg.get("mention_role_weight", 1.0)),
        mention_span_weight=float(loss_cfg.get("mention_span_weight", 1.0)),
        no_object_weight=float(loss_cfg.get("no_object_weight", 0.2)),
        no_mention_weight=float(loss_cfg.get("no_mention_weight", 0.2)),
    )

    no_object_id = smell2id["NO_OBJECT"]
    no_mention_id = role2id["NO_MENTION"]

    grad_accum = int(train_cfg.get("grad_accum_steps", 1))
    max_grad_norm = float(train_cfg.get("max_grad_norm", 1.0))

    def run_eval(epoch: int) -> float:
        model.eval()
        losses: List[float] = []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = torch.tensor(batch["input_ids"], device=device)
                attn = torch.tensor(batch["attention_mask"], device=device)
                outs = model(input_ids=input_ids, attention_mask=attn)
                for b in range(input_ids.size(0)):
                    loss = compute_set_loss(
                        outs.type_logits[b],
                        outs.mention_role_logits[b],
                        outs.mention_start_logits[b],
                        outs.mention_end_logits[b],
                        gold=batch["gold"][b],
                        no_object_id=no_object_id,
                        no_mention_id=no_mention_id,
                        cfg=loss_conf,
                    )
                    losses.append(float(loss.detach().cpu()))
        model.train()
        return float(np.mean(losses)) if losses else 0.0

    # Training loop
    model.train()
    if freeze_encoder:
        # Keep dropout disabled in the frozen encoder.
        model.encoder.eval()
    global_step = 0
    for epoch in range(1, int(train_cfg["epochs"]) + 1):
        pbar = tqdm(train_loader, desc=f"epoch {epoch}")
        running: List[float] = []
        opt.zero_grad(set_to_none=True)

        for it, batch in enumerate(pbar, start=1):
            input_ids = torch.tensor(batch["input_ids"], device=device)
            attn = torch.tensor(batch["attention_mask"], device=device)
            outs = model(input_ids=input_ids, attention_mask=attn)

            # Compute per-sample loss (matching is per sample)
            loss_batch = torch.tensor(0.0, device=device)
            for b in range(input_ids.size(0)):
                loss_batch = loss_batch + compute_set_loss(
                    outs.type_logits[b],
                    outs.mention_role_logits[b],
                    outs.mention_start_logits[b],
                    outs.mention_end_logits[b],
                    gold=batch["gold"][b],
                    no_object_id=no_object_id,
                    no_mention_id=no_mention_id,
                    cfg=loss_conf,
                )
            loss_batch = loss_batch / max(1, input_ids.size(0))
            loss_batch = loss_batch / grad_accum
            loss_batch.backward()

            if it % grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(trainable_params, max_grad_norm)
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
                global_step += 1

            running.append(float(loss_batch.detach().cpu()) * grad_accum)
            if running:
                pbar.set_postfix({"loss": sum(running[-20:]) / min(20, len(running))})

        val_loss = run_eval(epoch)
        if freeze_encoder:
            model.encoder.eval()
        with open(os.path.join(out_dir, "metrics.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"epoch": epoch, "val_loss": val_loss}) + "\n")

        if epoch % int(train_cfg.get("save_every", 1)) == 0:
            ckpt = {
                "epoch": epoch,
                "model_state": model.state_dict(),
                "optimizer_state": opt.state_dict(),
                "scheduler_state": sched.state_dict(),
                "config": cfg,
            }
            torch.save(ckpt, os.path.join(out_dir, f"checkpoint_epoch_{epoch}.pt"))

    print(f"done. checkpoints in {out_dir}")


if __name__ == "__main__":
    main()

