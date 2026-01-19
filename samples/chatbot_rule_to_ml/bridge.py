import graph
import shared


class IntentRoute:
    def __init__(self, name):
        self.name = name
        self.graph_seed = graph.GraphBuilder(2).seed

    def score(self):
        return 0.0


class IntentHandler:
    def __init__(self, name):
        self.name = name

    def score(self):
        return 0.0


class IntentPlanner:
    def __init__(self, name):
        self.name = name

    def score(self):
        return 0.0
