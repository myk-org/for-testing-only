class DataProcessor:
    def __init__(self):
        self.source = "dev"

    def transform(self, items):
        result = []
        for item in items:
            result.append(item.strip().upper())
        return result

    def run(self):
        data = ["hello ", " world", " dev "]
        return self.transform(data)
