class Router:
    def __init__(self, prefix="/api/v1"):
        self.routes = {}
        self.prefix = prefix
        self.middleware = []

    def add(self, path, handler):
        full_path = self.prefix + path
        self.routes[full_path] = handler

    def use(self, middleware_fn):
        self.middleware.append(middleware_fn)

    def match(self, path):
        handler = self.routes.get(path)
        if handler and self.middleware:
            for mw in self.middleware:
                handler = mw(handler)
        return handler
