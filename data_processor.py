class DataProcessor:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        self.data = []
        self.processed_count = 0

    def process(self, items, filter_fn=None):
        result = []
        for item in items:
            if filter_fn and not filter_fn(item):
                continue
            if item.is_valid():
                transformed = self._transform(item)
                result.append(transformed)
                self.processed_count += 1
        if self.logger:
            self.logger.info(f"Processed {self.processed_count} items")
        return result

    def _transform(self, item):
        return {
            "id": item.id,
            "value": item.value * 2,
            "timestamp": item.created_at,
        }

    def export(self, format="json", pretty=False):
        import json
        indent = 2 if pretty else None
        return json.dumps(self.data, indent=indent)

    def get_stats(self):
        return {"total": len(self.data), "processed": self.processed_count}

    def validate(self):
        return len(self.data) > 0 and self.processed_count >= 0
