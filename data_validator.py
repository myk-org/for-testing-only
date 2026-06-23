import logging

class DataValidator:
    def __init__(self, rules, logger=None, cache_results=False):
        self.rules = rules
        self.logger = logger or logging.getLogger(__name__)
        self.cache_results = cache_results
        self._cache = {}
        self.validation_count = 0

    def validate(self, data, strict=False):
        cache_key = str(data) if self.cache_results else None
        if cache_key and cache_key in self._cache:
            self.logger.debug("Cache hit for validation")
            return self._cache[cache_key]

        errors = []
        for rule in self.rules:
            try:
                if not rule(data):
                    errors.append(str(rule))
            except Exception as ex:
                if strict:
                    raise
                errors.append(f"Rule failed with error: {ex}")

        self.validation_count += 1
        self.logger.info(f"Validated item {self.validation_count}: {len(errors)} errors")

        if cache_key:
            self._cache[cache_key] = errors
        return errors

    def is_valid(self, data, strict=False):
        return len(self.validate(data, strict=strict)) == 0

    def validate_batch(self, items):
        results = {}
        for i, item in enumerate(items):
            results[i] = self.validate(item)
        self.logger.info(f"Batch validated {len(items)} items")
        return results

    def get_stats(self):
        return {
            "total_validations": self.validation_count,
            "cache_size": len(self._cache),
            "rules_count": len(self.rules),
        }

    def clear_cache(self):
        self._cache.clear()
        self.logger.debug("Validation cache cleared")
