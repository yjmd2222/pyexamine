from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
from .models import Ticket
from .storage import load_tickets, save_tickets
from .router import route

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="incident-portal")
    p.add_argument("--db", type=Path, default=Path("./data/tickets.json"))
    p.add_argument("--channel", choices=["ops","security","general"], default="general")
    p.add_argument("--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--id", required=True)
    a.add_argument("--category", required=True)
    a.add_argument("--summary", required=True)

    sub.add_parser("list")
    sub.add_parser("dispatch")
    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tickets = load_tickets(args.db)

    if args.cmd == "add":
        t = Ticket(
            id=args.id,
            created_at=datetime.now(),
            category=args.category,
            summary=args.summary,
            payload={"source":"cli"},
        )
        tickets.append(t)
        save_tickets(args.db, tickets)
        return 0

    if args.cmd == "list":
        for t in tickets:
            print(f"{t.id}	{t.category}	{t.summary}")
        return 0

    if args.cmd == "dispatch":
        for t in tickets:
            # control coupling via channel/verbose flags
            print(route(t, channel=args.channel, verbose=args.verbose))
        return 0

    raise SystemExit("unreachable")
