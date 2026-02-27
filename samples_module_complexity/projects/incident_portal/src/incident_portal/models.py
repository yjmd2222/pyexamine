from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Ticket:
    id: str
    created_at: datetime
    category: str
    summary: str
    payload: dict
