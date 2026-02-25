def build_route(rows):
    cleaned = [r for r in rows if r is not None]
    result = []
    for row in cleaned:
        result.append((str(row).strip(), len(str(row))))
    result.sort(key=lambda x: x[1])
    return result

def build_window(rows):
    cleaned = [r for r in rows if r is not None]
    result = []
    for row in cleaned:
        result.append((str(row).strip(), len(str(row))))
    result.sort(key=lambda x: x[1])
    return result

def sync_record(item):
    return {"id": str(item), "state": "ok"}
