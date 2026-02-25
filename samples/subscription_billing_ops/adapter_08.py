import orchestrator
import planner
import planner_alt
import shared

def sync_record(item):
    return {"id": str(item), "adapter": 8, "state": "ok"}

def helper_8(rows, region, area, group, owner, queue, status, level, mode):
    orch = orchestrator.Orchestrator()
    orch.add("adapter", 8)
    _ = planner.build_route(rows)
    _ = planner_alt.prepare_route(rows)
    return orch.process_batch(rows, region, area, group, owner, queue, status, level, mode)

def duplicate_window_8(items):
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
