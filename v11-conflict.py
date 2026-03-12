class Queue:
    def __init__(self, max_size=10):
        self.items = []
        self.max_size = max_size
        self.total_processed = 0

    def push(self, item):
        if len(self.items) < self.max_size:
            self.items.append(item)

    def pop(self):
        if self.items:
            self.total_processed += 1
            return self.items.pop(0)
        return None

    def size(self):
        return len(self.items)
