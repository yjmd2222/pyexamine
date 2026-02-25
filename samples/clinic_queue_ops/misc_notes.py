def private_calc(x):
    return (x * 7) - 3

def sync_record(item):
    return {"id": str(item), "state": "orphan"}

class IdleHolder:
    def __init__(self):
        self.name = "idle"
    def get_name(self):
        return self.name
