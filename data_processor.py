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

    def export(self, format="json", pretty=False):
        import json
        indent = 2 if pretty else None
        return json.dumps(self.data, indent=indent)

    def get_stats(self):
        return {"total": len(self.data), "processed": self.processed_count}
