
from typing import cast
from bus import OutputPin, SoftwareSPI
from config import register_configurable_entity, get_required_configurable_entity_by_name, TYPE_RUNTIME, TYPE_EXPORTER, TYPE_TAG_PROCESSOR, TYPE_RFID_READER, ConfigurableEntity
from config.configuration import Configuration
from controllers.moonraker_remote_method import MoonrakerRemoteMethodController
from exporters.webhook import WebhookExporter
from reader.fm175xx.rfid import Fm175xx
from reader.gpio_enabled_rfid_reader import GpioEnabledRfidReader
import time
import logging
import requests
from runtime import Runtime
import sys
import os
import json
import threading
import configparser

from tag.anycubic import AnycubicTagProcessor
from tag.bambu import BambuTagProcessor
from tag.creality import CrealityTagProcessor
from tag.elegoo import ElegooTagProcessor
from tag.openspool import OpenspoolTagProcessor
from tag.qidi.processor import QidiTagProcessor
from tag.snapmaker import SnapmakerTagProcessor
from tag.spoolease import SpooleaseTagProcessor
from tag.tigertag import TigerTagProcessor
from controllers.moonraker_on_property_change import MoonrakerOnPropertyChangeController

def consume_config(config: dict) -> Runtime:
    for key, value in config.items():
        configurable_entity = create_configurable_entity(key, value)
        register_configurable_entity(configurable_entity)

    return Runtime()

def create_configurable_entity(key: str, config: dict) -> ConfigurableEntity:
    key_split = key.split(" ", 2)
    name = key_split[1] if len(key_split) > 1 else key_split[0]
    config["__name"] = name

    match key_split[0]:
        case "configuration":
            return Configuration(config)
        case "output_pin":
            return OutputPin(config)
        case "software_spi":
            return SoftwareSPI(config)
        case "fm175xx":
            return Fm175xx(config)
        case "gpio_enabled_rfid_reader":
            return GpioEnabledRfidReader(config)
        case "bambu_lab_tag_processor":
            return BambuTagProcessor(config)
        case "anycubic_tag_processor":
            return AnycubicTagProcessor(config)
        case "creality_tag_processor":
            return CrealityTagProcessor(config)
        case "openspool_tag_processor":
            return OpenspoolTagProcessor(config)
        case "spoolease_tag_processor":
            return SpooleaseTagProcessor(config)
        case "snapmaker_tag_processor":
            return SnapmakerTagProcessor(config)
        case "tigertag_tag_processor":
            return TigerTagProcessor(config)
        case "elegoo_tag_processor":
            return ElegooTagProcessor(config)
        case "qidi_tag_processor":
            return QidiTagProcessor(config)
        case "webhook_exporter":
            return WebhookExporter(config)
        case "moonraker_remote_method":
            return MoonrakerRemoteMethodController(config)
        case "moonraker_on_property_change":
            return MoonrakerOnPropertyChangeController(config)
        case _:
            raise ValueError(f"Unknown configurable entity type: {key_split[0]}")

logging.basicConfig(level=logging.DEBUG)

def main():
    if len(sys.argv) < 2:
        logging.error("No config file provided")
        sys.exit(1)

    config_file = sys.argv[1]

    if not os.path.exists(config_file):
        logging.error(f"Config file does not exist: {config_file}")
        sys.exit(1)

    if config_file.endswith(".json"):
        with open(config_file, "r") as f:
            config = f.read()

        json_config = json.loads(config)

        run = consume_config(json_config)
    elif config_file.endswith(".ini") or config_file.endswith(".cfg"):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(config_file)

        config = {str(section): dict(parser.items(section)) for section in parser.sections()}

        run = consume_config(config)
    else:
        logging.error("Unsupported config file format, only .json is supported")
        sys.exit(1)

    for controller in run.controllers:
        threading.Thread(target=controller.loop, daemon=True).start()

    run.loop()

if __name__ == "__main__":
    main()
