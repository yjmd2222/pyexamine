"""Data containers and domain models."""


class Ingredient:
    def __init__(self, name, unit):
        self.name = name
        self.unit = unit

    def key(self):
        return f"{self.name}:{self.unit}"


class Recipe:
    def __init__(self, name, ingredients):
        self.name = name
        self.ingredients = list(ingredients)

    def size(self):
        return len(self.ingredients)


class Meal:
    def __init__(self, name, recipe):
        self.name = name
        self.recipe = recipe

    def label(self):
        return f"{self.name}:{self.recipe.name}"


class PantryItem:
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount

    def update(self, delta):
        self.amount += delta


class Report:
    def __init__(self):
        self.lines = []

    def add_line(self, text):
        self.lines.append(text)

    def dump(self):
        return "\n".join(self.lines)
