class Queue:
    def __init__(self, max_size=50):
        self.items = []
        self.max_size = max_size
        self.total_processed = 0

    def push(self, item):
        self.items.append(item)
        if len(self.items) > self.max_size:
            self.items.pop(0)

    def pop(self):
        self.total_processed += 1
        return self.items.pop(0) if self.items else None

    def size(self):
        return len(self.items)
