from __future__ import annotations
from collections import Counter
from datetime import datetime

def count_by_service(rows: list[tuple[datetime, str, str]]) -> dict[str, int]:
    c: Counter[str] = Counter()
    for _, service, _ in rows:
        c[service] += 1
    return dict(c)

def top_messages(rows: list[tuple[datetime, str, str]], *, n: int = 3) -> list[str]:
    c: Counter[str] = Counter()
    for _, _, msg in rows:
        c[msg] += 1
    return [m for m, _ in c.most_common(n)]
