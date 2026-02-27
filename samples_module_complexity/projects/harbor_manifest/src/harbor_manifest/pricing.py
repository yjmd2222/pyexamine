from __future__ import annotations
from .types import Shipment

def quote_usd(shipment: Shipment, *, rate_per_kg: float = 1.25, rate_per_m3: float = 45.0) -> float:
    # keep computation local to this module
    return shipment.total_weight_kg * rate_per_kg + shipment.total_volume_m3 * rate_per_m3
