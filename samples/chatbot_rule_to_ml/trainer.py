import math
import shared


def train_model(samples):
    total = 0
    for sample in samples:
        total += math.sqrt(len(sample))
    return total
