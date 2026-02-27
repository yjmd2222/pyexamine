from __future__ import annotations
import json
from .types import Item, Shipment

def load_shipment(text: str) -> Shipment:
    data = json.loads(text)
    items = tuple(
        Item(
            sku=str(x["sku"]),
            weight_kg=float(x["weight_kg"]),
            volume_m3=float(x["volume_m3"]),
        )
        for x in data["items"]
    )
    return Shipment(
        origin=str(data["origin"]),
        destination=str(data["destination"]),
        items=items,
    )
