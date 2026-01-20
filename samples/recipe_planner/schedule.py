"""Schedule assembly for meal slots."""

import inventory
from planner import Slot


class SlotAllocator:
    def __init__(self):
        self.cursor = 0

    def next_slot(self, name):
        slot = Slot(name, self.cursor)
        self.cursor += 1
        return slot


def build_schedule(book):
    allocator = SlotAllocator()
    availability = inventory.availability_map()
    slots = []
    for name in book.list_recipes():
        if availability.get(name, True):
            slots.append(allocator.next_slot(name))
    return slots
