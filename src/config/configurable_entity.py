from abc import ABC
import logging

class ConfigurableEntity(ABC):
    def __init__(self, config: dict, type : str):
        self.name = config["__name"]
        self.type = type
        self.config = config
        self.enabled = str(config.get("enabled", "true")).lower() == "true"
        self.logger = logging.getLogger(f"{self.type}:{self.name}")

    def get_str_array_from_config(self, key: str, optional : bool) -> list[str]:
        if optional and key not in self.config:
            return []

        value = self.config[key]
        if isinstance(value, list):
            return [str(item) for item in value]
        elif isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        else:
            raise ValueError(f"Invalid config value for key '{key}': expected string or list of strings")