class DataValidator:
    def __init__(self, rules):
        self.rules = rules

    def validate(self, data):
        errors = []
        for rule in self.rules:
            if not rule(data):
                errors.append(str(rule))
        return errors

    def is_valid(self, data):
        return len(self.validate(data)) == 0
