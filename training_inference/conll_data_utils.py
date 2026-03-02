from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .data_utils import (
    DatasetBuildOutput,
    build_label_maps,
    build_smell_maps,
    downsample_negatives,
    save_split_manifests,
    stratified_split,
)


@dataclass
class RawConllExample:
    id: int
    smell_name: str
    is_detected: bool
    text: str
    tokens: List[str]
    labels: List[Any]
    raw: Dict[str, Any]
    headers: Dict[str, Any]
    source_dataset_path: Optional[str] = None
    source_local_id: Optional[int] = None


def _unescape_conll_token(token: str) -> str:
    out: List[str] = []
    i = 0
    while i < len(token):
        ch = token[i]
        if ch != "\\" or i + 1 >= len(token):
            out.append(ch)
            i += 1
            continue
        nxt = token[i + 1]
        if nxt == "t":
            out.append("\t")
        elif nxt == "n":
            out.append("\n")
        elif nxt == "r":
            out.append("\r")
        elif nxt == "\\":
            out.append("\\")
        else:
            out.append(nxt)
        i += 2
    return "".join(out)


def _parse_header_line(line: str) -> tuple[str, Any]:
    payload = line[2:] if line.startswith("# ") else line[1:]
    key, raw_value = payload.split(" = ", 1)
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value
    return key, value


def _parse_label(label_text: str) -> Any:
    if label_text == "-100":
        return -100
    return label_text


def parse_conll_block(
    lines: Sequence[str],
    source_path: Optional[Path] = None,
    block_index: int = 0,
) -> RawConllExample:
    headers: Dict[str, Any] = {}
    tokens: List[str] = []
    labels: List[Any] = []

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if not line:
            continue
        if line.startswith("#"):
            key, value = _parse_header_line(line)
            headers[key] = value
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            location = f"{source_path}:{block_index}" if source_path is not None else f"block {block_index}"
            raise ValueError(f"Malformed CoNLL row in {location}: {line!r}")
        token_text, label_text = parts
        tokens.append(_unescape_conll_token(token_text))
        labels.append(_parse_label(label_text))

    missing = [key for key in ("id", "smell_name", "is_detected") if key not in headers]
    if missing:
        location = str(source_path) if source_path is not None else f"block {block_index}"
        raise ValueError(f"Missing required headers {missing} in {location}")
    if not tokens:
        location = str(source_path) if source_path is not None else f"block {block_index}"
        raise ValueError(f"Empty CoNLL sample body in {location}")
    if len(tokens) != len(labels):
        location = str(source_path) if source_path is not None else f"block {block_index}"
        raise ValueError(f"Token/label length mismatch in {location}")

    source_str = str(source_path.resolve()) if source_path is not None else None
    sample_id = int(headers["id"])
    raw = {
        "headers": dict(headers),
        "source_dataset_path": source_str,
        "source_local_id": sample_id,
    }
    return RawConllExample(
        id=sample_id,
        smell_name=str(headers["smell_name"]),
        is_detected=bool(headers["is_detected"]),
        text=" ".join(tokens),
        tokens=tokens,
        labels=labels,
        raw=raw,
        headers=headers,
        source_dataset_path=source_str,
        source_local_id=sample_id,
    )


def load_conll_examples(conll_path: Path) -> List[RawConllExample]:
    examples: List[RawConllExample] = []
    lines = conll_path.read_text(encoding="utf-8").splitlines(keepends=True)
    current_block: List[str] = []
    block_index = 0

    def _flush() -> None:
        nonlocal block_index
        if not current_block:
            return
        examples.append(parse_conll_block(current_block, source_path=conll_path, block_index=block_index))
        current_block.clear()
        block_index += 1

    for line in lines:
        if line.strip():
            current_block.append(line)
        else:
            _flush()
    _flush()
    return examples


def load_conll_examples_many(conll_paths: Sequence[Path]) -> List[RawConllExample]:
    merged: List[RawConllExample] = []
    next_id = 0
    for path in conll_paths:
        for ex in load_conll_examples(path):
            raw = dict(ex.raw)
            raw["source_dataset_path"] = str(path.resolve())
            raw["source_local_id"] = ex.id
            merged.append(
                RawConllExample(
                    id=next_id,
                    smell_name=ex.smell_name,
                    is_detected=ex.is_detected,
                    text=ex.text,
                    tokens=list(ex.tokens),
                    labels=list(ex.labels),
                    raw=raw,
                    headers=dict(ex.headers),
                    source_dataset_path=str(path.resolve()),
                    source_local_id=ex.id,
                )
            )
            next_id += 1
    return merged


def resolve_strict_conll_entries(
    repo_root: Path,
    dataset_root_dir: str = "cdatasets",
    conll_name: str = "role_section_excerpts.line.conll",
) -> List[Dict[str, str]]:
    root = (repo_root / dataset_root_dir).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Dataset root dir not found: {root}")

    entries: List[Dict[str, str]] = []
    missing: List[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        conll_path = child / conll_name
        if conll_path.exists():
            entries.append(
                {
                    "dataset_name": child.name,
                    "conll_path": str(conll_path.resolve()),
                }
            )
        else:
            missing.append(f"{child.name}: missing {conll_name}")
    if missing:
        raise FileNotFoundError(
            "Strict CoNLL dataset structure violation under "
            f"{root}:\n" + "\n".join(missing)
        )
    return entries


def create_conll_dataset_build(
    repo_root: Path,
    dataset_root_dir: str = "cdatasets",
    conll_name: str = "role_section_excerpts.line.conll",
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
    train_neg_pos_ratio: Optional[float] = None,
    balance_per_smell: bool = False,
    split_manifest_dir: Optional[Path] = None,
) -> DatasetBuildOutput:
    repo_root = repo_root.resolve()
    entries = resolve_strict_conll_entries(
        repo_root=repo_root,
        dataset_root_dir=dataset_root_dir,
        conll_name=conll_name,
    )
    conll_paths = [Path(row["conll_path"]) for row in entries]
    examples = load_conll_examples_many(conll_paths)

    label_maps = build_label_maps(examples)
    smell_maps = build_smell_maps(examples)
    split = stratified_split(
        examples,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )
    balanced_train = downsample_negatives(
        split.train,
        neg_pos_ratio=train_neg_pos_ratio,
        seed=seed,
        per_smell=balance_per_smell,
    )
    balanced_split = type(split)(train=balanced_train, val=split.val, test=split.test)

    if split_manifest_dir is not None:
        save_split_manifests(balanced_split, split_manifest_dir)

    return DatasetBuildOutput(
        train_examples=balanced_split.train,
        val_examples=balanced_split.val,
        test_examples=balanced_split.test,
        label_maps=label_maps,
        smell_maps=smell_maps,
    )


def summarize_conll_examples(examples: Sequence[RawConllExample]) -> Dict[str, Any]:
    pos = sum(1 for ex in examples if ex.is_detected)
    neg = len(examples) - pos
    smells = sorted({ex.smell_name for ex in examples})
    lengths = [len(ex.tokens) for ex in examples]
    return {
        "num_examples": len(examples),
        "num_positive": pos,
        "num_negative": neg,
        "num_smells": len(smells),
        "smells": smells,
        "avg_tokens": (sum(lengths) / len(lengths)) if lengths else 0.0,
        "max_tokens": max(lengths) if lengths else 0,
    }
