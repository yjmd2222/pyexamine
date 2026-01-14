class HabitBase:
    def __init__(self, name: str):
        self.name = name

    def label(self):
        return self.name.title()


class HabitDaily(HabitBase):
    def cadence(self):
        return "daily"


class HabitWeekly(HabitDaily):
    def cadence(self):
        return "weekly"


class HabitMonthly(HabitWeekly):
    def cadence(self):
        return "monthly"


class HabitAnnual(HabitMonthly):
    def cadence(self):
        return "annual"
