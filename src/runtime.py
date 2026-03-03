from config import TYPE_CONTROLLER, TYPE_CONFIGURATION, get_required_configurable_entity_by_name, TYPE_EXPORTER, TYPE_TAG_PROCESSOR, TYPE_RFID_READER, get_entities_by_type
from config.configuration import default_configuration, Configuration
from controllers.controller import Controller
from tag.tag_types import TagType
from tag.tag_processor import TagProcessor
from tag.mifare_classic_tag_processor import MifareClassicTagProcessor
from tag.mifare_ultralight_tag_processor import MifareUltralightTagProcessor
from reader.mifare_classic_reader import MifareClassicReader
from reader.mifare_ultralight_reader import MifareUltralightReader
from reader.rfid_reader import RfidReader
from exporters.exporter import Exporter
from reader.scan_result import ScanResult
from filament import GenericFilament
from typing import cast
import time
import logging

class Runtime:
    def __init__(self):
        configs = cast(list[Configuration], get_entities_by_type(TYPE_CONFIGURATION))

        if len(configs) == 0:
            configs = [default_configuration()]
        elif len(configs) >= 2:
            logging.warning(f"Multiple configurations found, using the first one: {[config.name for config in configs]}")

        self.config = configs[0]

        self.rfid_readers : list[RfidReader] = [x for x in cast(list[RfidReader], get_entities_by_type(TYPE_RFID_READER)) if x.enabled]
        self.tag_processors : list[TagProcessor] = [x for x in cast(list[TagProcessor], get_entities_by_type(TYPE_TAG_PROCESSOR)) if x.enabled]
        self.exporters : list[Exporter] = [x for x in cast(list[Exporter], get_entities_by_type(TYPE_EXPORTER)) if x.enabled and not x.error_exporter]
        self.error_exporters : list[Exporter] = [x for x in cast(list[Exporter], get_entities_by_type(TYPE_EXPORTER)) if x.enabled and x.error_exporter]
        self.controllers : list[Controller] = [x for x in cast(list[Controller], get_entities_by_type(TYPE_CONTROLLER)) if x.enabled]

        for controller in self.controllers:
            controller.runtime = self # type: ignore

        self.mifare_classic_processors = [processor for processor in self.tag_processors if isinstance(processor, MifareClassicTagProcessor)]
        self.mifare_ultralight_processors = [processor for processor in self.tag_processors if isinstance(processor, MifareUltralightTagProcessor)]

        self.read_retries_left = [0] * len(self.rfid_readers)

    def start_reading_tag(self, slot: int):
        if slot < 0 or slot >= len(self.rfid_readers):
            logging.error(f"Invalid slot number: {slot}")
            return
        
        self.read_retries_left[slot] = self.config.read_retries
        logging.info(f"Started reading tag on slot {slot} with {self.config.read_retries} retries")

    def loop(self):
        while True:
            for i, reader in enumerate(self.rfid_readers):
                if self.config.auto_read_mode or self.read_retries_left[i] > 0:
                    result = self.process_reader_single(reader)
                    self.read_retries_left[i] -= 1
                    scan_result = None

                    if result is not None:
                        scan_result, filament = result
                        if filament is not None:
                            logging.info(f"Processed tag with UID {scan_result.uid} into filament: {filament}")

                            for exporter in self.exporters:
                                exporter.export_data(scan_result, filament, reader)

                        self.read_retries_left[i] = 0

                    elif self.read_retries_left[i] <= 0 and not self.config.auto_read_mode:
                        logging.warning(f"Failed to read from reader {reader.name}, no retries left")
                        self.read_retries_left[i] = 0

                        for exporter in self.error_exporters:
                            exporter.export_data(scan_result, None, reader)

            time.sleep(self.config.read_interval_seconds)
        
    def process_reader_single(self, reader: RfidReader) -> tuple[ScanResult, GenericFilament|None]|None:
        reader.start_session()
        scan_result = reader.scan()
        reader.end_session()
        if scan_result is None:
            logging.debug("No tag detected")
            return
        
        uid = scan_result.uid.hex()
        
        if self.config.auto_read_mode and reader.is_same_tag(uid):
            logging.debug("Same tag detected as last read, skipping processing")
            return
        
        logging.info(f"Detected tag type {scan_result.tag_type.name} with UID {scan_result.uid.hex().upper()}")

        filament = None
        if scan_result.tag_type == TagType.MifareClassic1k and isinstance(reader, MifareClassicReader):
            filament = self.process_mifare_classic(reader, scan_result)
        elif scan_result.tag_type == TagType.MifareUltralight and isinstance(reader, MifareUltralightReader):
            filament = self.process_mifare_ultralight(reader, scan_result)
        
        if filament is None:
            logging.warning("Failed to read data from tag")
            return (scan_result, None)
        
        logging.info(filament.pretty_text())
        
        reader.set_last_read_uid(uid)
        return (scan_result, filament)

    def process_mifare_classic(self, reader: MifareClassicReader, scan_result: ScanResult) -> GenericFilament | None:
        for processor in self.mifare_classic_processors:
            reader.start_session()

            if reader.scan() == None:
                logging.warning("Tag lost before reading")
                reader.end_session()
                continue

            logging.debug(f"Attempting to read with processor: {processor.name}")
            auth = processor.authenticate_tag(scan_result)

            if auth is None:
                logging.warning("Authentication failed with processor, skipping processor")
                reader.end_session()
                continue

            card_data = reader.read_mifare_classic(scan_result, auth)
            reader.end_session()

            if card_data is not None:
                logging.debug(f"Read MIFARE Classic card data: {card_data.hex().upper()}")
                return processor.process_tag(scan_result, card_data)
            else:
                logging.warning("Failed to read MIFARE Classic card data")
                continue

        return None
    
    def process_mifare_ultralight(self, reader: MifareUltralightReader, scan_result: ScanResult) -> GenericFilament | None:
        reader.start_session()

        if reader.scan() == None:
            logging.warning("Tag lost before reading")
            reader.end_session()
            return None

        card_data = reader.read_mifare_ultralight(scan_result)
        reader.end_session()

        if card_data is not None:
            logging.debug(f"Read MIFARE Ultralight card data: {card_data.hex().upper()}")

            for processor in self.mifare_ultralight_processors:
                logging.debug(f"Attempting to read with processor: {processor.name}")
                filament = processor.process_tag(scan_result, card_data)

                if filament is not None:
                    return filament
        else:
            logging.warning("Failed to read MIFARE Ultralight card data")

        return None