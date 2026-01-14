import json
import shared


def run_model(samples):
    total = 0
    for sample in samples:
        total += len(json.dumps(sample))
    return total
