from __future__ import annotations
from datetime import date
from .models import PhotoRecord

def scan_paths(paths: list[str]) -> list[PhotoRecord]:
    # pretend "taken_on" is derived from a filename pattern.
    out: list[PhotoRecord] = []
    for p in paths:
        taken_on: date | None = None
        parts = p.replace("\\", "/").split("/")
        name = parts[-1]
        if len(name) >= 10 and name[4] == "-" and name[7] == "-":
            try:
                taken_on = date.fromisoformat(name[:10])
            except ValueError:
                taken_on = None
        out.append(PhotoRecord(path=p, taken_on=taken_on, tags=[]))
    return out
