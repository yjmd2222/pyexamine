from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
from .bootstrap import load_settings, prime_cache
from .planner import next_run
from .notifier import format_message

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="launchpad-schedule")
    p.add_argument("--settings", type=Path, default=Path("./data/settings.json"))
    p.add_argument("--topic", default="daily sync")
    p.add_argument("cmd", choices=["plan","notify"])
    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_settings(args.settings)
    prime_cache()

    if args.cmd == "plan":
        print(next_run(datetime.now()).isoformat(timespec="seconds"))
        return 0

    if args.cmd == "notify":
        print(format_message(args.topic))
        return 0

    raise SystemExit("unreachable")
