from __future__ import annotations
from .types import Shipment

def select_route(shipment: Shipment) -> str:
    # simple heuristic, deliberately small interface
    if shipment.total_weight_kg > 800 or shipment.total_volume_m3 > 30:
        return "cargo-rail"
    if shipment.origin.split("-")[0] == shipment.destination.split("-")[0]:
        return "regional-truck"
    return "intermodal"
