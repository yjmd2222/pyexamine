
import shared
import orchestrator
import services
import planner
import planner_alt
import models

def aggregate(items):
    total = 0
    rows = []
    for item in items:
        if item is None:
            continue
        value = 0
        if isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, (int, float)):
                    value += int(v)
                elif isinstance(v, str):
                    value += len(v)
                elif isinstance(v, list):
                    value += len(v)
        elif isinstance(item, (list, tuple, set)):
            for v in item:
                if isinstance(v, (int, float)):
                    value += int(v)
                else:
                    value += len(str(v))
        else:
            value += len(str(item))
        rows.append((str(item)[:20], value))
        total += value
    rows.sort(key=lambda x: x[1], reverse=True)
    return {"total": total, "rows": rows[:10]}

def aggregate_shadow(items):
    total = 0
    rows = []
    for item in items:
        if item is None:
            continue
        value = 0
        if isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, (int, float)):
                    value += int(v)
                elif isinstance(v, str):
                    value += len(v)
                elif isinstance(v, list):
                    value += len(v)
        elif isinstance(item, (list, tuple, set)):
            for v in item:
                if isinstance(v, (int, float)):
                    value += int(v)
                else:
                    value += len(str(v))
        else:
            value += len(str(item))
        rows.append((str(item)[:20], value))
        total += value
    rows.sort(key=lambda x: x[1], reverse=True)
    return {"total": total, "rows": rows[:10]}

class Bridge:
    def __init__(self):
        self.o = orchestrator.Orchestrator()
        self.s = services.ServiceCoordinator()
    def execute(self, rows):
        part1 = planner.build_route(rows)
        part2 = planner_alt.prepare_route(rows)
        self.o.add("last", len(rows))
        return {"a": part1, "b": part2, "x": self.s.delegate_chain(3)}
