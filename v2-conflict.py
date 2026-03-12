class DataProcessor:
    def __init__(self):
        self.source = "main"
        self.validated = False

    def validate(self, items):
        self.validated = all(isinstance(i, str) for i in items)
        return self.validated

    def transform(self, items):
        return [i.strip().lower() for i in items]

    def run(self):
        data = ["Hello ", " World", " Main ", " Extra"]
        if self.validate(data):
            return self.transform(data)
        return []
