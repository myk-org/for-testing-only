class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.data = []
        self.processed_count = 0

    def process(self, items):
        result = []
        for item in items:
            if item.is_valid():
                result.append(self._transform(item))
        return result

    def _transform(self, item):
        return {"id": item.id, "value": item.value * 2}

    def export(self, format="json"):
        import json
        return json.dumps(self.data)

    def get_stats(self):
        return {"total": len(self.data), "processed": self.processed_count}

    def validate(self):
        return len(self.data) > 0 and self.processed_count >= 0
