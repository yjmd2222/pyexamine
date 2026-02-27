from __future__ import annotations
from datetime import datetime, timedelta
from . import state

def next_run(now: datetime | None = None) -> datetime:
    if now is None:
        now = datetime.now()
    interval_min = int(state.get_setting("interval_min", 15))
    return now + timedelta(minutes=interval_min)
