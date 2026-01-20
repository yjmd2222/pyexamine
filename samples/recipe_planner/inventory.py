"""Inventory helpers for pantry tracking."""

import planner


class PantryIndex:
    def __init__(self):
        self.items = {}

    def add(self, name, count):
        self.items[name] = self.items.get(name, 0) + count

    def has(self, name):
        return self.items.get(name, 0) > 0


class StockTracker:
    def __init__(self):
        self.records = []

    def record(self, item, qty):
        self.records.append((item, qty))

    def totals(self):
        return {item: qty for item, qty in self.records}


def availability_map():
    board = planner.PlanBoard("inventory")
    board.add_slot(planner.Slot("default", 0))
    return {slot.name: True for slot in board.slots}
