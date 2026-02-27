from __future__ import annotations
from .models import Album

def summarize(albums: list[Album]) -> str:
    lines: list[str] = []
    for a in albums:
        tagged = sum(1 for p in a.photos if p.tags)
        lines.append(f"{a.name}: {len(a.photos)} photos ({tagged} tagged)")
    return "\n".join(lines)
