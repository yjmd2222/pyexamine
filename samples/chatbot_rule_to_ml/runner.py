import json
import graph
import shared


def run_model(samples):
    total = 0
    total += graph.GraphBuilder(0).seed
    for sample in samples:
        total += len(json.dumps(sample))
    return total
