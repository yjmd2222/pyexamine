from __future__ import annotations
# content coupling: this module manipulates another module's internal variables and calls internal function
from . import core

def apply_adjustment(sku: str, delta: int) -> None:
    core._inventory[sku] = int(core._inventory.get(sku, 0)) + int(delta)
    core._recalc()

def set_price(sku: str, new_price: float) -> None:
    core._prices[sku] = float(new_price)
    core._recalc()
