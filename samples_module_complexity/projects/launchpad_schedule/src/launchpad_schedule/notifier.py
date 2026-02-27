from __future__ import annotations
from . import state

def format_message(topic: str) -> str:
    prefix = str(state.get_setting("prefix", "[notice]"))
    if not state.CACHE.get("ready"):
        prefix = "[cold]"
    return f"{prefix} {topic}"
