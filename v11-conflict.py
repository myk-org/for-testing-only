class Queue:
    def __init__(self):
        self.items = []
        self.max_size = 10

    def push(self, item):
        if len(self.items) < self.max_size:
            self.items.append(item)

    def pop(self):
        if self.items:
            return self.items.pop(0)
        return None
