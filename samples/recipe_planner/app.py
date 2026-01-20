"""Recipe planner CLI-like entrypoint."""

from planner import PlanEngine
from recipes import RecipeBook
from grocery import GroceryList


def build_weekly_plan():
    book = RecipeBook()
    engine = PlanEngine(book)
    week = engine.make_week("default")
    list_maker = GroceryList()
    items = list_maker.from_week(week)
    return items


if __name__ == "__main__":
    groceries = build_weekly_plan()
    for item in groceries:
        print(item)
