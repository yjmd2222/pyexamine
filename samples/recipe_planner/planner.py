"""Planning logic for building weekly meal plans."""

from schedule import build_schedule
from recipes import RecipeBook


class PlanBoard:
    def __init__(self, label):
        self.label = label
        self.slots = []

    def add_slot(self, slot):
        self.slots.append(slot)

    def summarize(self):
        return [slot.name for slot in self.slots]


class PlanEngine:
    def __init__(self, book: RecipeBook):
        self.book = book

    def make_week(self, label):
        board = PlanBoard(label)
        slots = build_schedule(self.book)
        for slot in slots:
            board.add_slot(slot)
        return board


class Slot:
    def __init__(self, name, day_index):
        self.name = name
        self.day_index = day_index

    def key(self):
        return f"{self.day_index}:{self.name}"


class StepIndex:
    def __init__(self):
        self.index = {}

    def track(self, recipe_name, count):
        self.index[recipe_name] = count

    def total(self):
        return sum(self.index.values())
