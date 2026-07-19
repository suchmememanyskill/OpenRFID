from .configurable_entity import ConfigurableEntity
from . import TYPE_CONFIGURATION

class Configuration(ConfigurableEntity):
    def __init__(self, config : dict):
        super().__init__(config, TYPE_CONFIGURATION)

        self.auto_read_mode = str(config.get("auto_read_mode", "false")).lower() == "true"
        self.read_interval_seconds = float(config.get("read_interval_seconds", 1))
        self.read_retries = int(config.get("retries", 3))

        # Filament type normaliser — resolves non-standard types (PLA+, ABS+, …)
        # to valid VALID_BASE_MATERIALS entries before GenericFilament raises ValueError.
        #
        # strip_plus:    ABS+ → ABS, PLA+ → PLA   (strips trailing '+')
        # prefix_match:  PETG-RAPID → PETG         (longest-prefix match)
        # type_map:      explicit overrides, comma-separated key:value pairs
        #                e.g. "ABS-PLUS:ABS, SILK-PLA:PLA"
        self.type_normalizer_strip_plus   = str(config.get("type_normalizer_strip_plus",   "false")).lower() == "true"
        self.type_normalizer_prefix_match = str(config.get("type_normalizer_prefix_match", "false")).lower() == "true"

        raw_map = str(config.get("type_normalizer_type_map", ""))
        self.type_normalizer_type_map: dict[str, str] = {}
        if raw_map.strip():
            for pair in raw_map.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, _, v = pair.partition(":")
                    self.type_normalizer_type_map[k.strip().upper()] = v.strip()

def default_configuration() -> Configuration:
    return Configuration({
        "__name": TYPE_CONFIGURATION,
    })