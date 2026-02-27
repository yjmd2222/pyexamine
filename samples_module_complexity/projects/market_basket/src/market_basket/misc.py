from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def today_stamp() -> str:
    return datetime.now().strftime("%Y%m%d")

def compact(s: str) -> str:
    return " ".join(s.split())
