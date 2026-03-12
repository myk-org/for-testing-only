class Router:
    def __init__(self):
        self.routes = {}
        self.prefix = "/api/v1"

    def add(self, path, handler):
        full_path = self.prefix + path
        self.routes[full_path] = handler

    def match(self, path):
        return self.routes.get(path)
