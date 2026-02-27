from __future__ import annotations
from .models import PhotoRecord

def apply_tags(records: list[PhotoRecord], rules: dict[str, list[str]]) -> None:
    # stamp coupling: entire records passed around and mutated
    for r in records:
        for key, tags in rules.items():
            if key in r.path:
                for t in tags:
                    if t not in r.tags:
                        r.tags.append(t)
