from __future__ import annotations
import json
from pathlib import Path
from . import state

def load_settings(path: Path) -> None:
    # temporal cohesion: startup-only actions grouped here
    data = json.loads(path.read_text(encoding="utf-8"))
    for k, v in data.items():
        state.set_setting(k, v)

def prime_cache() -> None:
    # shared cache used by other modules
    state.CACHE["ready"] = True
