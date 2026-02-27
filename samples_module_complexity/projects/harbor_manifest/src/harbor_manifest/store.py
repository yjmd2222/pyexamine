from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from .types import Store

class LocalStore(Store):
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def list_manifests(self) -> Iterable[str]:
        if not self._base_dir.exists():
            return []
        return sorted(p.name for p in self._base_dir.glob("*.json"))

    def read_manifest(self, name: str) -> str:
        path = self._base_dir / name
        return path.read_text(encoding="utf-8")
