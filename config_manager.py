import os

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = {}

    def load(self):
        with open(self.config_path) as f:
            for line in f:
                key, value = line.strip().split("=", 1)
                self.data[key] = value
        return self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def save(self):
        with open(self.config_path, "w") as f:
            for key, value in self.data.items():
                f.write(f"{key}={value}\n")
