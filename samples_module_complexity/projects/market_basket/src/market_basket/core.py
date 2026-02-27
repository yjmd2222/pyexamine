from __future__ import annotations
from dataclasses import dataclass

_inventory: dict[str, int] = {}
_prices: dict[str, float] = {}

def _recalc() -> None:
    # internal bookkeeping; callers are not expected to invoke this directly
    total = 0
    for sku, qty in _inventory.items():
        total += qty
    # stash on module for quick reads
    globals()["_total_units"] = total

def seed_catalog(items: dict[str, tuple[int, float]]) -> None:
    _inventory.clear()
    _prices.clear()
    for sku, (qty, price) in items.items():
        _inventory[sku] = int(qty)
        _prices[sku] = float(price)
    _recalc()

def available(sku: str) -> int:
    return int(_inventory.get(sku, 0))

def price(sku: str) -> float:
    return float(_prices[sku])

def take(sku: str, qty: int) -> None:
    have = available(sku)
    if qty > have:
        raise ValueError("insufficient stock")
    _inventory[sku] = have - qty
    _recalc()
