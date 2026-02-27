from __future__ import annotations
import argparse
from pathlib import Path
from .pipeline import summarize

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="log-tally")
    p.add_argument("--input", type=Path, default=Path("./data/sample.log"))
    p.add_argument("cmd", choices=["summary"])
    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = args.input.read_text(encoding="utf-8")
    print(summarize(text))
    return 0
