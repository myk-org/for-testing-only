class Cache:
    def __init__(self, max_size=100):
        self.store = {}
        self.misses = 0
        self.max_size = max_size

    def get(self, key):
        if key not in self.store:
            self.misses += 1
            return None
        return self.store[key]

    def set(self, key, value):
        if len(self.store) >= self.max_size:
            oldest = next(iter(self.store))
            del self.store[oldest]
        self.store[key] = value

    def clear(self):
        self.store.clear()
        self.misses = 0
