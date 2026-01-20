"""Recipe storage and retrieval."""


class RecipeBook:
    def __init__(self):
        self._recipes = [
            "pasta_bowl",
            "rice_plate",
            "salad_box",
            "soup_pot",
        ]

    def list_recipes(self):
        return list(self._recipes)

    def has(self, name):
        return name in self._recipes


class PortionScaler:
    def __init__(self, base_size=2):
        self.base_size = base_size

    def scale(self, target):
        return max(1, int(target / self.base_size))


class Metric:
    def __init__(self, label, value):
        self.label = label
        self.value = value

    def as_tuple(self):
        return (self.label, self.value)
