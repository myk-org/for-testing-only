import os
import json
import logging
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path, env_prefix=None, logger=None):
        self.config_path = Path(config_path)
        self.env_prefix = env_prefix
        self.logger = logger or logging.getLogger(__name__)
        self.data = {}
        self._validators = {}
        self._defaults = {}
        self._loaded = False

    def load(self, merge_env=True):
        if not self.config_path.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            self.data = dict(self._defaults)
            self._loaded = True
            return self.data

        with open(self.config_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                self.data[key.strip()] = value.strip()

        if merge_env and self.env_prefix:
            for env_key, env_value in os.environ.items():
                if env_key.startswith(self.env_prefix):
                    config_key = env_key[len(self.env_prefix):].lower()
                    self.data[config_key] = env_value
                    self.logger.debug(f"Env override: {config_key}")

        self._loaded = True
        self.logger.info(f"Loaded {len(self.data)} config entries")
        return self.data

    def get(self, key, default=None):
        return self.data.get(key, default or self._defaults.get(key))

    def set_default(self, key, value):
        self._defaults[key] = value

    def add_validator(self, key, validator_fn):
        self._validators[key] = validator_fn

    def validate(self):
        errors = []
        for key, validator in self._validators.items():
            value = self.data.get(key)
            if value is not None and not validator(value):
                errors.append(f"Validation failed for {key}: {value}")
                self.logger.error(f"Config validation failed: {key}={value}")
        return errors

    def reload(self):
        self.data.clear()
        return self.load()

    def save(self, format="env"):
        if format == "json":
            with open(self.config_path, "w") as f:
                json.dump(self.data, f, indent=2)
        else:
            with open(self.config_path, "w") as f:
                for key, value in sorted(self.data.items()):
                    f.write(f"{key}={value}\n")
        self.logger.info(f"Saved {len(self.data)} config entries as {format}")

    def get_stats(self):
        return {
            "entries": len(self.data),
            "defaults": len(self._defaults),
            "validators": len(self._validators),
            "loaded": self._loaded,
        }
