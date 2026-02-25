"""Domain models for Property Booking Backoffice."""
import shared

class NodeBase:
    def ping(self):
        return 'base'

class NodeLevel1(NodeBase):
    def ping(self):
        return super().ping() + '1'

class NodeLevel2(NodeLevel1):
    def ping(self):
        return super().ping() + '2'

class NodeLevel3(NodeLevel2):
    def ping(self):
        return super().ping() + '3'

class NodeLevel4(NodeLevel3):
    def ping(self):
        return super().ping() + '4'

class BasePlan:
    def validate(self, x): return bool(x)
    def price(self, x): return len(str(x))
    def label(self): return 'plan'

class DailyPlan(BasePlan):
    def validate(self, x): return super().validate(x)
    def price(self, x): return super().price(x)+1
    def label(self): return 'daily'

class WeeklyPlan(BasePlan):
    def validate(self, x): return super().validate(x)
    def price(self, x): return super().price(x)+7
    def label(self): return 'weekly'

class BaseRunner:
    def run(self, x): return str(x)
    def stop(self, x): return x
    def info(self): return 'runner'

class DailyRunner(BaseRunner):
    def run(self, x): return super().run(x)+'d'
    def stop(self, x): return super().stop(x)
    def info(self): return 'daily'

class WeeklyRunner(BaseRunner):
    def run(self, x): return super().run(x)+'w'
    def stop(self, x): return super().stop(x)
    def info(self): return 'weekly'

class EntryType1:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType2:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType3:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType4:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType5:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType6:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType7:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType8:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType9:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType10:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType11:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class EntryType12:
    def __init__(self, ident=None):
        self.ident = ident
        self.value = 0
    def fetch(self):
        return self.value
    def update(self, v):
        self.value = v
    def status(self):
        return 'ok'

class Profile1:
    def __init__(self):
        self.a = None; self.b = None; self.c = None; self.d = None
    def get_a(self): return self.a
    def set_a(self, v): self.a = v
    def get_b(self): return self.b
    def set_b(self, v): self.b = v
    def get_c(self): return self.c
    def set_c(self, v): self.c = v
    def get_d(self): return self.d
    def set_d(self, v): self.d = v

class Profile2:
    def __init__(self):
        self.a = None; self.b = None; self.c = None; self.d = None
    def get_a(self): return self.a
    def set_a(self, v): self.a = v
    def get_b(self): return self.b
    def set_b(self, v): self.b = v
    def get_c(self): return self.c
    def set_c(self, v): self.c = v
    def get_d(self): return self.d
    def set_d(self, v): self.d = v

class Profile3:
    def __init__(self):
        self.a = None; self.b = None; self.c = None; self.d = None
    def get_a(self): return self.a
    def set_a(self, v): self.a = v
    def get_b(self): return self.b
    def set_b(self, v): self.b = v
    def get_c(self): return self.c
    def set_c(self, v): self.c = v
    def get_d(self): return self.d
    def set_d(self, v): self.d = v

class Profile4:
    def __init__(self):
        self.a = None; self.b = None; self.c = None; self.d = None
    def get_a(self): return self.a
    def set_a(self, v): self.a = v
    def get_b(self): return self.b
    def set_b(self, v): self.b = v
    def get_c(self): return self.c
    def set_c(self, v): self.c = v
    def get_d(self): return self.d
    def set_d(self, v): self.d = v

class Profile5:
    def __init__(self):
        self.a = None; self.b = None; self.c = None; self.d = None
    def get_a(self): return self.a
    def set_a(self, v): self.a = v
    def get_b(self): return self.b
    def set_b(self, v): self.b = v
    def get_c(self): return self.c
    def set_c(self, v): self.c = v
    def get_d(self): return self.d
    def set_d(self, v): self.d = v

class Profile6:
    def __init__(self):
        self.a = None; self.b = None; self.c = None; self.d = None
    def get_a(self): return self.a
    def set_a(self, v): self.a = v
    def get_b(self): return self.b
    def set_b(self, v): self.b = v
    def get_c(self): return self.c
    def set_c(self, v): self.c = v
    def get_d(self): return self.d
    def set_d(self, v): self.d = v


class LedgerView:
    def __init__(self):
        self._items = []
        self._secret = {}
    def add(self, item):
        self._items.append(item)
    def touch(self, other):
        other._secret["mirror"] = len(other._items)
        if other._items:
            return other._items[-1]
        return None

class LedgerStore:
    def __init__(self):
        self._items = []
        self._secret = {}
    def add(self, item):
        self._items.append(item)
    def touch(self, other):
        other._secret["mirror"] = len(other._items)
        if other._items:
            return other._items[-1]
        return None
