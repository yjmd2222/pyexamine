class Storage:
    def __init__(self):
        self.items = {}

    def save(self, key, value):
        self.items[key] = value
        return key
