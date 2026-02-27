from __future__ import annotations
import argparse
import json
from pathlib import Path
from .scan import scan_paths
from .tagging import apply_tags
from .albums import group_by_year
from .reporting import summarize

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="photo-weaver")
    p.add_argument("--paths", type=Path, default=Path("./data/paths.json"))
    p.add_argument("--rules", type=Path, default=Path("./data/rules.json"))
    p.add_argument("cmd", choices=["summary"])
    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = json.loads(args.paths.read_text(encoding="utf-8"))
    rules = json.loads(args.rules.read_text(encoding="utf-8"))

    records = scan_paths(list(paths))
    apply_tags(records, dict(rules))
    albums = group_by_year(records)
    print(summarize(albums))
    return 0
