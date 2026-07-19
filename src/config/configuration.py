from .configurable_entity import ConfigurableEntity
from . import TYPE_CONFIGURATION

class Configuration(ConfigurableEntity):
    def __init__(self, config : dict):
        super().__init__(config, TYPE_CONFIGURATION)

        self.auto_read_mode = str(config.get("auto_read_mode", "false")).lower() == "true"
        self.read_interval_seconds = float(config.get("read_interval_seconds", 1))
        self.read_retries = int(config.get("retries", 3))

def default_configuration() -> Configuration:
    return Configuration({
        "__name": TYPE_CONFIGURATION,
    })