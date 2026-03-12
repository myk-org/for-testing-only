class Cache:
    def __init__(self):
        self.store = {}
        self.hits = 0

    def get(self, key):
        if key in self.store:
            self.hits += 1
            return self.store[key]
        return None

    def set(self, key, value):
        self.store[key] = value
