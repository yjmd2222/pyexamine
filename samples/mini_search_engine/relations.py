class ProfileState:
    def __init__(self, balance, status, limit, tier):
        self.balance = balance
        self.status = status
        self.limit = limit
        self.tier = tier


class ProfileInspector:
    def balance(self, state: ProfileState):
        return state.balance

    def status(self, state: ProfileState):
        return state.status

    def limit(self, state: ProfileState):
        return state.limit

    def tier(self, state: ProfileState):
        return state.tier
