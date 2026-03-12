class Parser:
    def __init__(self, encoding="utf-8"):
        self.strict = True
        self.encoding = encoding
        self.errors = []

    def parse(self, text):
        try:
            lines = text.encode(self.encoding).decode(self.encoding).strip().split("\n")
            return [line.strip() for line in lines if line.strip()]
        except UnicodeError as e:
            self.errors.append(str(e))
            return []

    def validate(self, text):
        return len(text) > 0 and self.strict

    def has_errors(self):
        return len(self.errors) > 0
