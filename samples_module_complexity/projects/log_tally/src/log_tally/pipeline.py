from __future__ import annotations
from .extract import parse_lines
from .transform import count_by_service, top_messages
from .report import render

def summarize(text: str) -> str:
    rows = parse_lines(text)
    counts = count_by_service(rows)
    top = top_messages(rows, n=3)
    return render(counts, top)
