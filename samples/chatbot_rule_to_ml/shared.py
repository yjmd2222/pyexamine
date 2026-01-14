import math
import json


def shared_score(payload):
    return math.sqrt(len(json.dumps(payload)))
