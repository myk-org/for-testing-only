class Parser:
    def __init__(self):
        self.strict = True

    def parse(self, text):
        lines = text.strip().split("\n")
        return [line.strip() for line in lines if line.strip()]

    def validate(self, text):
        return len(text) > 0 and self.strict
