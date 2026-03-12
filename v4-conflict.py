class Cache:
    def __init__(self, max_size=100):
        self.store = {}
        self.hits = 0
        self.max_size = max_size

    def get(self, key):
        if key in self.store:
            self.hits += 1
            return self.store[key]
        return None

    def set(self, key, value):
        if len(self.store) >= self.max_size:
            oldest = next(iter(self.store))
            del self.store[oldest]
        self.store[key] = value

    def clear(self):
        self.store.clear()
        self.hits = 0
