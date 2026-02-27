from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Iterable

@dataclass(frozen=True)
class Item:
    sku: str
    weight_kg: float
    volume_m3: float

@dataclass(frozen=True)
class Shipment:
    origin: str
    destination: str
    items: tuple[Item, ...]

    @property
    def total_weight_kg(self) -> float:
        return sum(i.weight_kg for i in self.items)

    @property
    def total_volume_m3(self) -> float:
        return sum(i.volume_m3 for i in self.items)

class Store(Protocol):
    def list_manifests(self) -> Iterable[str]: ...
    def read_manifest(self, name: str) -> str: ...
