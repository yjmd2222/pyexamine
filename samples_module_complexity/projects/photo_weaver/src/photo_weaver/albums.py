from __future__ import annotations
from collections import defaultdict
from .models import PhotoRecord, Album

def group_by_year(records: list[PhotoRecord]) -> list[Album]:
    buckets: dict[str, list[PhotoRecord]] = defaultdict(list)
    for r in records:
        year = str(r.taken_on.year) if r.taken_on else "unknown"
        buckets[year].append(r)
    return [Album(name=k, photos=v) for k, v in sorted(buckets.items())]
