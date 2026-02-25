class C:
    def __init__(self, value):
        self.value = value
    def end(self):
        return self.value
    def next(self):
        return self

class B:
    def __init__(self, value):
        self.value = value
    def next(self):
        return C(self.value)

class A:
    def __init__(self, value):
        self.value = value
    def next(self):
        return B(self.value)
