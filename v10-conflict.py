class Parser:
    def __init__(self, encoding="utf-8"):
        self.encoding = encoding
        self.errors = []

    def parse(self, text):
        try:
            return text.encode(self.encoding).decode(self.encoding).split("\n")
        except UnicodeError as e:
            self.errors.append(str(e))
            return []

    def has_errors(self):
        return len(self.errors) > 0
