"""Grocery list generation."""


class GroceryList:
    def __init__(self):
        self.items = []

    def add(self, name):
        self.items.append(name)

    def from_week(self, board):
        for name in board.summarize():
            self.add(name)
        return list(self.items)


class Shopper:
    def __init__(self):
        self.history = []

    def record(self, item):
        self.history.append(item)

    def last(self):
        return self.history[-1] if self.history else None
