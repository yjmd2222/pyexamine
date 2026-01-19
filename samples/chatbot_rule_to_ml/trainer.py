import graph
import math
import shared


def train_model(samples):
    total = 0
    total += graph.GraphBuilder(1).seed
    for sample in samples:
        total += math.sqrt(len(sample))
    return total
