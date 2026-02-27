from __future__ import annotations
from .core import available, price, take

def total(cart: dict[str, int]) -> float:
    # data coupling: cart is a basic mapping
    return sum(price(sku) * qty for sku, qty in cart.items())

def purchase(cart: dict[str, int]) -> float:
    for sku, qty in cart.items():
        if available(sku) < qty:
            raise ValueError(f"missing {sku}")
    for sku, qty in cart.items():
        take(sku, qty)
    return total(cart)
