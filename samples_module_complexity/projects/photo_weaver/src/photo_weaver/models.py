from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass
class PhotoRecord:
    path: str
    taken_on: date | None
    tags: list[str]

@dataclass
class Album:
    name: str
    photos: list[PhotoRecord]
