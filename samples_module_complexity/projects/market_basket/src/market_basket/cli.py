from __future__ import annotations
import argparse
import json
from pathlib import Path
from .core import seed_catalog, available
from .checkout import purchase
from .backoffice import apply_adjustment

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="market-basket")
    p.add_argument("--catalog", type=Path, default=Path("./data/catalog.json"))
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stock").add_argument("sku")
    buy = sub.add_parser("buy")
    buy.add_argument("--cart", type=Path, required=True)

    adj = sub.add_parser("adjust")
    adj.add_argument("sku")
    adj.add_argument("delta", type=int)
    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    items = json.loads(args.catalog.read_text(encoding="utf-8"))
    seed_catalog({k: (v["qty"], v["price"]) for k, v in items.items()})

    if args.cmd == "stock":
        print(available(args.sku))
        return 0

    if args.cmd == "buy":
        cart = json.loads(args.cart.read_text(encoding="utf-8"))
        print(f"{purchase({k:int(v) for k, v in cart.items()}):.2f}")
        return 0

    if args.cmd == "adjust":
        apply_adjustment(args.sku, args.delta)
        print("ok")
        return 0

    raise SystemExit("unreachable")
