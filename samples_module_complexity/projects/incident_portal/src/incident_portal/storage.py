from __future__ import annotations
import json
from pathlib import Path
from .models import Ticket
from datetime import datetime

def load_tickets(path: Path) -> list[Ticket]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: list[Ticket] = []
    for r in raw:
        out.append(Ticket(
            id=str(r["id"]),
            created_at=datetime.fromisoformat(r["created_at"]),
            category=str(r["category"]),
            summary=str(r["summary"]),
            payload=dict(r.get("payload", {})),
        ))
    return out

def save_tickets(path: Path, tickets: list[Ticket]) -> None:
    raw = [{
        "id": t.id,
        "created_at": t.created_at.isoformat(timespec="seconds"),
        "category": t.category,
        "summary": t.summary,
        "payload": t.payload,
    } for t in tickets]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
