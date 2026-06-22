class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.data = []

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

    def reset(self):
        self.data = []
        self.processed_count = 0
