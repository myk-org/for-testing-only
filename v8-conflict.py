class Logger:
    def __init__(self, level="info"):
        self.level = level
        self.count = 0

    def log(self, msg):
        self.count += 1
        return f"[{self.level}] #{self.count}: {msg}"

    def reset(self):
        self.count = 0
