from __future__ import annotations
import argparse
import json
from pathlib import Path
from .store import LocalStore
from .manifest_loader import load_shipment
from .pricing import quote_usd
from .routing import select_route

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harbor-manifest")
    p.add_argument("--data-dir", type=Path, default=Path("./data"))
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    q = sub.add_parser("quote")
    q.add_argument("name", help="manifest file name, e.g., sample.json")

    r = sub.add_parser("route")
    r.add_argument("name", help="manifest file name, e.g., sample.json")
    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = LocalStore(args.data_dir)

    if args.cmd == "list":
        for n in store.list_manifests():
            print(n)
        return 0

    text = store.read_manifest(args.name)
    shipment = load_shipment(text)

    if args.cmd == "quote":
        print(f"{quote_usd(shipment):.2f}")
        return 0

    if args.cmd == "route":
        print(select_route(shipment))
        return 0

    raise SystemExit("unreachable")
