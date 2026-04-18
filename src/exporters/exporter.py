from config import ConfigurableEntity, TYPE_EXPORTER
from abc import abstractmethod

from filament.generic import GenericFilament
from reader.rfid_reader import RfidReader
from reader.scan_result import ScanResult
from enum import Enum

class ExporterEvent(Enum):
    TAG_READ = "tag_read"
    TAG_PARSE_ERROR = "tag_parse_error"
    TAG_NOT_PRESENT = "tag_not_present"

class Exporter(ConfigurableEntity):
    def __init__(self, config: dict):
        super().__init__(config, TYPE_EXPORTER)
        self.events = [ExporterEvent(event) for event in self.get_str_array_from_config("events", True) if isinstance(event, str)]

        event = config.get("event", "").lower()
        if event:
            self.events = [ExporterEvent(event)]

        if not self.events:
            self.logger.error(f"Exporter '{self.name}' must have at least one event specified in the configuration")

    def has_event(self, event: ExporterEvent) -> bool:
        """Evaluates whether this exporter has the specified event configured."""
        return event in self.events

    @abstractmethod
    def export_data(self, scan: ScanResult|None, filament: GenericFilament|None, reader : RfidReader):
        """Exports the given filament data associated with a scan result. The scan and filament may be None if the export is triggered by a read error or unrecognized tag."""
        raise NotImplementedError("Subclasses must implement this method")