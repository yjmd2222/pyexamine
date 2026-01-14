class Cache:
    def __init__(self):
        self._data = {}

    def remember(self, key, value):
        self._data[key] = value
        return value
