class DataProcessor:
    def __init__(self):
        self.source = "dev"
        self.validated = False

    def validate(self, items):
        self.validated = all(isinstance(i, str) for i in items)
        return self.validated

    def transform(self, items):
        result = []
        for item in items:
            result.append(item.strip().upper())
        return result

    def run(self):
        data = ["hello ", " world", " dev "]
        if self.validate(data):
            return self.transform(data)
        return []
