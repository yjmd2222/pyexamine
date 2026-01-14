class QueryStore:
    def __init__(self):
        self.history = []

    def add(self, query: str):
        self.history.append(query)
        return len(self.history)
