from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import torch
from torch.utils.data import Dataset

IGNORE_INDEX = -100


@dataclass
class RawExample:
    id: int
    smell_name: str
    is_detected: bool
    text: str
    tokens: List[str]
    labels: List[Any]
    raw: Dict[str, Any]


@dataclass
class SplitResult:
    train: List[RawExample]
    val: List[RawExample]
    test: List[RawExample]


@dataclass
class LabelMaps:
    label_to_id: Dict[str, int]
    id_to_label: Dict[int, str]
    ignore_index: int = IGNORE_INDEX


@dataclass
class SmellMaps:
    smell_to_head: Dict[str, int]
    head_to_smell: Dict[int, str]


@dataclass
class DatasetBuildOutput:
    train_examples: List[RawExample]
    val_examples: List[RawExample]
    test_examples: List[RawExample]
    label_maps: LabelMaps
    smell_maps: SmellMaps


def resolve_dataset_path(repo_root: Path, preferred_name: str = "role_section_excerpts.line.jsonl") -> Path:
    """Resolve the requested dataset path with a clear fallback for older exports.

    The user asked for `role_section_excerpts.line.jsonl`. Some repos may only contain
    `role_section_excerpts.jsonl` (same content shape for token-level training). We fall back
    explicitly instead of silently searching random files.
    """
    preferred = repo_root / preferred_name
    if preferred.exists():
        return preferred

    fallback = repo_root / "role_section_excerpts.jsonl"
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        f"Could not find {preferred_name!r} or fallback 'role_section_excerpts.jsonl' under {repo_root}"
    )


def resolve_strict_dataset_entries(
    repo_root: Path,
    dataset_root_dir: str = "datasets",
    excerpt_name: str = "excerpt.jsonl",
    sidecar_name: str = "sidecar.jsonl",
) -> List[Dict[str, str]]:
    """Return strict per-dataset entries from `<repo_root>/<dataset_root_dir>/*/`.

    Strict means each dataset directory must contain BOTH `excerpt_name` and `sidecar_name`.
    No fallback filename behavior is applied.
    """
    root = (repo_root / dataset_root_dir).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Dataset root dir not found: {root}")

    entries: List[Dict[str, str]] = []
    missing: List[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        excerpt = child / excerpt_name
        sidecar = child / sidecar_name
        if excerpt.exists() and sidecar.exists():
            entries.append(
                {
                    "dataset_name": child.name,
                    "excerpt_path": str(excerpt.resolve()),
                    "sidecar_path": str(sidecar.resolve()),
                }
            )
        else:
            missing_parts: List[str] = []
            if not excerpt.exists():
                missing_parts.append(excerpt_name)
            if not sidecar.exists():
                missing_parts.append(sidecar_name)
            missing.append(f"{child.name}: missing {', '.join(missing_parts)}")
    if missing:
        raise FileNotFoundError(
            "Strict dataset structure violation under "
            f"{root}:\n" + "\n".join(missing)
        )
    return entries


def generate_dataset_paths_config(
    repo_root: Path,
    output_path: Path,
    dataset_root_dir: str = "datasets",
    excerpt_name: str = "excerpt.jsonl",
    sidecar_name: str = "sidecar.jsonl",
) -> Dict[str, Any]:
    """Generate strict dataset path config JSON for training/inference scripts."""
    repo_root = repo_root.resolve()
    dataset_entries = resolve_strict_dataset_entries(
        repo_root=repo_root,
        dataset_root_dir=dataset_root_dir,
        excerpt_name=excerpt_name,
        sidecar_name=sidecar_name,
    )

    payload = {
        "repo_root": str(repo_root),
        "dataset_root_dir": dataset_root_dir,
        "excerpt_name": excerpt_name,
        "sidecar_name": sidecar_name,
        "mode": "strict_per_dataset",
        "datasets": dataset_entries,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_dataset_paths_from_config(config_path: Path) -> List[Path]:
    """Load excerpt JSONL paths from strict dataset config."""
    obj = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Invalid dataset config (expected object): {config_path}")
    datasets = obj.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError(f"Invalid dataset config (missing non-empty datasets): {config_path}")
    paths: List[Path] = []
    for row in datasets:
        if not isinstance(row, dict):
            raise ValueError(f"Invalid dataset row in config: {row!r}")
        excerpt = row.get("excerpt_path")
        sidecar = row.get("sidecar_path")
        if not excerpt or not sidecar:
            raise ValueError(f"Invalid dataset row (requires excerpt_path + sidecar_path): {row!r}")
        paths.append(Path(str(excerpt)).resolve())
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Some dataset paths in config do not exist:\n" + "\n".join(missing)
        )
    return paths


def _normalize_label_value(value: Any) -> Any:
    if value == -100:
        return -100
    if isinstance(value, int) and value == IGNORE_INDEX:
        return IGNORE_INDEX
    return str(value)


def load_role_section_examples(jsonl_path: Path, fail_fast: bool = True) -> List[RawExample]:
    examples: List[RawExample] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            obj = json.loads(line)
            missing = [k for k in ["id", "smell_name", "is_detected", "text", "tokens", "labels"] if k not in obj]
            if missing:
                raise ValueError(f"Missing keys {missing} at line {line_num} in {jsonl_path}")
            tokens = list(obj["tokens"])
            labels = [_normalize_label_value(v) for v in obj["labels"]]
            if fail_fast and len(tokens) != len(labels):
                raise ValueError(
                    f"Token/label length mismatch at line {line_num}: {len(tokens)} tokens vs {len(labels)} labels"
                )
            examples.append(
                RawExample(
                    id=int(obj["id"]),
                    smell_name=str(obj["smell_name"]),
                    is_detected=bool(obj["is_detected"]),
                    text=str(obj["text"]),
                    tokens=tokens,
                    labels=labels,
                    raw=obj,
                )
            )
    return examples


def load_role_section_examples_many(
    jsonl_paths: Sequence[Path],
    fail_fast: bool = True,
) -> List[RawExample]:
    """Load and merge multiple excerpt JSONL files, remapping IDs to unique global IDs."""
    merged: List[RawExample] = []
    next_id = 0
    for path in jsonl_paths:
        for ex in load_role_section_examples(path, fail_fast=fail_fast):
            raw = dict(ex.raw)
            raw["source_dataset_path"] = str(path)
            raw["source_local_id"] = ex.id
            merged.append(
                RawExample(
                    id=next_id,
                    smell_name=ex.smell_name,
                    is_detected=ex.is_detected,
                    text=ex.text,
                    tokens=ex.tokens,
                    labels=ex.labels,
                    raw=raw,
                )
            )
            next_id += 1
    return merged


def build_label_maps(examples: Sequence[RawExample]) -> LabelMaps:
    observed: set[str] = set()
    for ex in examples:
        for lb in ex.labels:
            if lb == IGNORE_INDEX:
                continue
            if not isinstance(lb, str):
                raise ValueError(f"Unexpected non-string label (except -100): {lb!r}")
            observed.add(lb)

    # Deterministic ordering: O first, then B-ROLE0/I-ROLE0/B-ROLE1/I-ROLE1/..., then any extras.
    def label_sort_key(label: str) -> Tuple[int, int, int, str]:
        if label == "O":
            return (0, 0, 0, label)
        if "-" in label:
            prefix, rest = label.split("-", 1)
            prefix_order = {"B": 0, "I": 1}.get(prefix, 2)
            role_num = 999
            if rest.startswith("ROLE"):
                try:
                    role_num = int(rest.replace("ROLE", ""))
                except ValueError:
                    role_num = 999
            return (1, role_num, prefix_order, label)
        return (2, 999, 9, label)

    ordered = sorted(observed, key=label_sort_key)
    label_to_id = {lb: i for i, lb in enumerate(ordered)}
    id_to_label = {i: lb for lb, i in label_to_id.items()}
    return LabelMaps(label_to_id=label_to_id, id_to_label=id_to_label, ignore_index=IGNORE_INDEX)


def build_smell_maps(examples: Sequence[RawExample]) -> SmellMaps:
    smells = sorted({ex.smell_name for ex in examples})
    smell_to_head = {name: i for i, name in enumerate(smells)}
    head_to_smell = {i: name for name, i in smell_to_head.items()}
    return SmellMaps(smell_to_head=smell_to_head, head_to_smell=head_to_smell)


def stratified_split(
    examples: Sequence[RawExample],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> SplitResult:
    total = train_ratio + val_ratio + test_ratio
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-8):
        raise ValueError(f"Split ratios must sum to 1.0 (got {total})")

    rng = random.Random(seed)
    buckets: Dict[Tuple[str, bool], List[RawExample]] = {}
    for ex in examples:
        buckets.setdefault((ex.smell_name, ex.is_detected), []).append(ex)

    train: List[RawExample] = []
    val: List[RawExample] = []
    test: List[RawExample] = []

    for key in sorted(buckets.keys()):
        bucket = list(buckets[key])
        rng.shuffle(bucket)
        n = len(bucket)

        # Round in a stable way, while keeping at least one item when possible.
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        if n_train + n_val > n:
            n_val = max(0, n - n_train)
        n_test = n - n_train - n_val

        # Adjust tiny buckets to avoid negative counts or impossible allocation.
        if n >= 3 and n_test == 0 and test_ratio > 0:
            if n_train > n_val and n_train > 1:
                n_train -= 1
                n_test += 1
            elif n_val > 0:
                n_val -= 1
                n_test += 1
        if n >= 2 and n_val == 0 and val_ratio > 0:
            if n_train > 1:
                n_train -= 1
                n_val += 1
            elif n_test > 1:
                n_test -= 1
                n_val += 1

        train.extend(bucket[:n_train])
        val.extend(bucket[n_train : n_train + n_val])
        test.extend(bucket[n_train + n_val :])

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return SplitResult(train=train, val=val, test=test)


def downsample_negatives(
    examples: Sequence[RawExample],
    neg_pos_ratio: Optional[float],
    seed: int = 42,
    per_smell: bool = False,
) -> List[RawExample]:
    """Downsample `is_detected=False` examples while keeping all positives.

    Parameters
    ----------
    neg_pos_ratio:
        None -> no balancing.
        1.0 -> keep at most one negative per positive.
        2.0 -> keep at most two negatives per positive.
    per_smell:
        If True, apply the ratio independently within each smell bucket. If a smell bucket has
        zero positives, we keep all negatives for that smell (to avoid wiping out a head entirely).
    """
    if neg_pos_ratio is None:
        return list(examples)
    if neg_pos_ratio < 0:
        raise ValueError("neg_pos_ratio must be >= 0")

    rng = random.Random(seed)

    def _balance(bucket: List[RawExample]) -> List[RawExample]:
        pos = [e for e in bucket if e.is_detected]
        neg = [e for e in bucket if not e.is_detected]
        if not neg:
            return list(bucket)
        if not pos:
            # No positives => ratio is undefined. Keep the negatives so the smell still trains on O tokens.
            return list(bucket)
        max_neg = int(len(pos) * neg_pos_ratio)
        max_neg = max(0, min(max_neg, len(neg)))
        rng.shuffle(neg)
        kept_neg = neg[:max_neg]
        out = pos + kept_neg
        rng.shuffle(out)
        return out

    if per_smell:
        groups: Dict[str, List[RawExample]] = {}
        for ex in examples:
            groups.setdefault(ex.smell_name, []).append(ex)
        result: List[RawExample] = []
        for smell in sorted(groups.keys()):
            result.extend(_balance(groups[smell]))
        rng.shuffle(result)
        return result

    return _balance(list(examples))


def save_split_manifests(split: SplitResult, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for split_name, items in [("train", split.train), ("val", split.val), ("test", split.test)]:
        payload = [
            {
                "id": ex.id,
                "smell_name": ex.smell_name,
                "is_detected": ex.is_detected,
            }
            for ex in items
        ]
        (out_dir / f"{split_name}_manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def create_dataset_build(
    repo_root: Path,
    preferred_dataset_name: str = "role_section_excerpts.line.jsonl",
    dataset_config_path: Optional[Path] = None,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
    train_neg_pos_ratio: Optional[float] = None,
    balance_per_smell: bool = False,
    split_manifest_dir: Optional[Path] = None,
) -> DatasetBuildOutput:
    if dataset_config_path is not None:
        dataset_paths = load_dataset_paths_from_config(dataset_config_path)
    else:
        dataset_paths = [resolve_dataset_path(repo_root, preferred_name=preferred_dataset_name)]

    if len(dataset_paths) == 1:
        examples = load_role_section_examples(dataset_paths[0])
    else:
        examples = load_role_section_examples_many(dataset_paths)
    label_maps = build_label_maps(examples)
    smell_maps = build_smell_maps(examples)
    split = stratified_split(examples, train_ratio=train_ratio, val_ratio=val_ratio, test_ratio=test_ratio, seed=seed)

    balanced_train = downsample_negatives(
        split.train,
        neg_pos_ratio=train_neg_pos_ratio,
        seed=seed,
        per_smell=balance_per_smell,
    )
    balanced_split = SplitResult(train=balanced_train, val=split.val, test=split.test)

    if split_manifest_dir is not None:
        save_split_manifests(balanced_split, split_manifest_dir)

    return DatasetBuildOutput(
        train_examples=balanced_split.train,
        val_examples=balanced_split.val,
        test_examples=balanced_split.test,
        label_maps=label_maps,
        smell_maps=smell_maps,
    )


def _convert_continuation_subtoken_label(label: str) -> str:
    """For subword continuations, convert B-ROLEX -> I-ROLEX to keep BIO consistency."""
    if label.startswith("B-"):
        return "I-" + label[2:]
    return label


def _require_fast_tokenizer(tokenizer: Any) -> None:
    if not getattr(tokenizer, "is_fast", False):
        raise ValueError(
            "A fast tokenizer is required for word_ids()-based label alignment. "
            "Use AutoTokenizer.from_pretrained(..., use_fast=True)."
        )


class PretokenizedSmellDataset(Dataset):
    """Dataset for token classification using pretokenized `tokens` + BIO labels.

    Input examples contain their own token list (`example.tokens`). The HF tokenizer can consume
    this with `is_split_into_words=True`, then we expand labels to subword pieces.
    """

    def __init__(
        self,
        examples: Sequence[RawExample],
        tokenizer: Any,
        label_maps: LabelMaps,
        smell_maps: SmellMaps,
        max_length: int = 8192,
        label_all_subtokens: bool = True,
        convert_b_to_i_on_subtoken: bool = True,
    ) -> None:
        _require_fast_tokenizer(tokenizer)
        self.examples = list(examples)
        self.tokenizer = tokenizer
        self.label_maps = label_maps
        self.smell_maps = smell_maps
        self.max_length = int(max_length)
        self.label_all_subtokens = bool(label_all_subtokens)
        self.convert_b_to_i_on_subtoken = bool(convert_b_to_i_on_subtoken)

    def __len__(self) -> int:
        return len(self.examples)

    def _tokenize_pretokenized(self, words: Sequence[str], truncation: bool) -> Any:
        return self.tokenizer(
            list(words),
            is_split_into_words=True,
            truncation=truncation,
            max_length=self.max_length,
            add_special_tokens=True,
            return_attention_mask=True,
            return_special_tokens_mask=True,
        )

    def _align_labels(self, example: RawExample, enc: Any) -> Tuple[List[int], List[Optional[int]], bool]:
        labels = example.labels
        word_ids = enc.word_ids()  # list[Optional[int]] length == seq_len
        aligned: List[int] = []
        prev_word_id: Optional[int] = None
        max_seen_word_id = -1

        for word_id in word_ids:
            if word_id is None:
                aligned.append(self.label_maps.ignore_index)
            else:
                max_seen_word_id = max(max_seen_word_id, word_id)
                raw_label = labels[word_id]
                if raw_label == self.label_maps.ignore_index:
                    aligned.append(self.label_maps.ignore_index)
                elif not self.label_all_subtokens and word_id == prev_word_id:
                    aligned.append(self.label_maps.ignore_index)
                else:
                    label_str = str(raw_label)
                    if word_id == prev_word_id and self.convert_b_to_i_on_subtoken:
                        label_str = _convert_continuation_subtoken_label(label_str)
                    if label_str not in self.label_maps.label_to_id:
                        raise ValueError(f"Unknown label after alignment: {label_str!r} (example id={example.id})")
                    aligned.append(self.label_maps.label_to_id[label_str])
            prev_word_id = word_id

        was_truncated = max_seen_word_id < (len(example.tokens) - 1)
        return aligned, list(word_ids), was_truncated

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        ex = self.examples[idx]

        # First pass with truncation for actual training/inference tensors.
        enc = self._tokenize_pretokenized(ex.tokens, truncation=True)
        aligned_labels, word_ids, was_truncated = self._align_labels(ex, enc)

        # Fail-fast alignment checks.
        seq_len = len(enc["input_ids"])
        if seq_len != len(aligned_labels):
            raise ValueError(
                f"Aligned label length mismatch for id={ex.id}: seq_len={seq_len}, labels={len(aligned_labels)}"
            )

        return {
            "id": ex.id,
            "smell_name": ex.smell_name,
            "is_detected": ex.is_detected,
            "text": ex.text,
            "raw_tokens": ex.tokens,
            "raw_labels": ex.labels,
            "smell_head_id": self.smell_maps.smell_to_head[ex.smell_name],
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
            "special_tokens_mask": enc.get("special_tokens_mask"),
            "labels": aligned_labels,
            "word_ids": word_ids,
            "was_truncated": was_truncated,
        }


class TokenClassificationCollator:
    """Pads variable-length encoded samples and preserves metadata lists for debug/inference."""

    def __init__(self, tokenizer: Any, label_pad_id: int = IGNORE_INDEX) -> None:
        self.tokenizer = tokenizer
        self.label_pad_id = int(label_pad_id)

    def __call__(self, batch: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        # Features consumed by tokenizer.pad must be simple dicts of tokenized fields.
        token_features = []
        label_lists = []
        for item in batch:
            token_features.append(
                {
                    "input_ids": item["input_ids"],
                    "attention_mask": item["attention_mask"],
                }
            )
            label_lists.append(item["labels"])

        padded = self.tokenizer.pad(token_features, padding=True, return_tensors="pt")
        max_len = padded["input_ids"].size(1)

        padded_labels = torch.full((len(batch), max_len), self.label_pad_id, dtype=torch.long)
        padded_special = torch.full((len(batch), max_len), 1, dtype=torch.long)
        for i, (labels, item) in enumerate(zip(label_lists, batch)):
            n = len(labels)
            padded_labels[i, :n] = torch.tensor(labels, dtype=torch.long)
            if item.get("special_tokens_mask") is not None:
                padded_special[i, :n] = torch.tensor(item["special_tokens_mask"], dtype=torch.long)

        return {
            "input_ids": padded["input_ids"],
            "attention_mask": padded["attention_mask"],
            "labels": padded_labels,
            "special_tokens_mask": padded_special,
            "smell_head_ids": torch.tensor([item["smell_head_id"] for item in batch], dtype=torch.long),
            # Metadata kept as python lists for output/debug.
            "ids": [item["id"] for item in batch],
            "smell_names": [item["smell_name"] for item in batch],
            "is_detected": [item["is_detected"] for item in batch],
            "texts": [item["text"] for item in batch],
            "raw_tokens": [item["raw_tokens"] for item in batch],
            "raw_labels": [item["raw_labels"] for item in batch],
            "word_ids": [item["word_ids"] for item in batch],
            "was_truncated": [item["was_truncated"] for item in batch],
        }


def create_tokenizer(backbone_name: str, use_fast: bool = True, truncation_side: str = "right") -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("transformers is required to create a tokenizer. Install with: pip install transformers") from exc

    tokenizer = AutoTokenizer.from_pretrained(backbone_name, use_fast=use_fast)
    tokenizer.truncation_side = truncation_side  # 'right' => truncate from end
    return tokenizer


def summarize_dataset(examples: Sequence[RawExample]) -> Dict[str, Any]:
    pos = sum(1 for e in examples if e.is_detected)
    neg = len(examples) - pos
    smells = sorted({e.smell_name for e in examples})
    return {
        "num_examples": len(examples),
        "positives": pos,
        "negatives": neg,
        "num_smells": len(smells),
        "smell_names": smells,
    }
