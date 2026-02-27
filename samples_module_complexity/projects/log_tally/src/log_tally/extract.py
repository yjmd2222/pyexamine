from __future__ import annotations
from datetime import datetime

def parse_lines(text: str) -> list[tuple[datetime, str, str]]:
    out: list[tuple[datetime, str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # format: 2026-02-01T10:00:00Z service message
        parts = line.split(" ", 2)
        if len(parts) != 3:
            continue
        ts = parts[0].replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        out.append((dt, parts[1], parts[2]))
    return out
