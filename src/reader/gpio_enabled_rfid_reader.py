from time import sleep

from reader.mifare_classic_reader import MifareClassicReader
from reader.mifare_ultralight_reader import MifareUltralightReader
from reader.rfid_reader import RfidReader
from reader.scan_result import ScanResult
from bus import OutputPin
from config import get_required_configurable_entity_by_name, TYPE_OUTPUT_PIN, TYPE_RFID_READER
from typing import cast

from tag.mifare_classic_tag_processor import TagAuthentication

class GpioEnabledRfidReader(MifareClassicReader, MifareUltralightReader):
    def __init__(self, config: dict):
        super().__init__(config)
        self.gpio_pins_high = self.get_str_array_from_config("gpio_pins_high", True)
        self.gpio_pins_low = self.get_str_array_from_config("gpio_pins_low", True)
        self.rfid_reader = cast(RfidReader, get_required_configurable_entity_by_name(config["rfid_reader"], TYPE_RFID_READER))

        self.gpio_high : list[OutputPin] = []
        self.gpio_low : list[OutputPin] = []

        for pin in self.gpio_pins_high:
            self.gpio_high.append(cast(OutputPin, get_required_configurable_entity_by_name(pin, TYPE_OUTPUT_PIN)))

        for pin in self.gpio_pins_low:
            self.gpio_low.append(cast(OutputPin, get_required_configurable_entity_by_name(pin, TYPE_OUTPUT_PIN)))

    def start_session(self):
        for pin in self.gpio_high:
            pin.set_high()
        
        for pin in self.gpio_low:
            pin.set_low()

        # Allow channel to settle after changing GPIO states
        sleep(0.100)

        self.rfid_reader.start_session()

    def end_session(self):
        self.rfid_reader.end_session()

    def scan(self) -> ScanResult | None:
        return self.rfid_reader.scan()
    
    def read_mifare_classic(self, scan_result : ScanResult, keys: TagAuthentication) -> bytes|None:
        if isinstance(self.rfid_reader, MifareClassicReader):
            return self.rfid_reader.read_mifare_classic(scan_result, keys)
        
        return None
    
    def read_mifare_ultralight(self, scan_result : ScanResult) -> bytes|None:
        if isinstance(self.rfid_reader, MifareUltralightReader):
            return self.rfid_reader.read_mifare_ultralight(scan_result)
        
        return None