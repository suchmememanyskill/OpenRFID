from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.mifare_ultralight_tag_processor import MifareUltralightTagProcessor
from tag.tag_types import TagType
import struct
import tag.binary as binary

# Adapted from https://github.com/DnG-Crafts/ACE-RFID

class AnycubicTagProcessor(MifareUltralightTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

    def process_tag(self, scan_result: ScanResult, data: bytes) -> GenericFilament | None:
        if scan_result.tag_type != TagType.MifareUltralight:
            raise ValueError("AnycubicTagProcessor can only process Mifare Ultralight tags")
        
        if len(data) != 192:
            return None
        
        if data[0x10:0x14] != b'\x7B\x00\x65\x00':
            return None
        
        sku = data[0x14:0x24].decode('ASCII').rstrip('\x00')
        brand = data[0x28:0x38].decode('ASCII').rstrip('\x00')
        filament_type = data[0x3C:0x4C].decode('ASCII').rstrip('\x00')
        filament_types = filament_type.replace("-", " ").split(" ")

        if filament_types[0].endswith("+"):
            filament_types[0] = filament_types[0][:-1]
            filament_types.append("+")

        a = data[0x50]
        b = data[0x51]
        g = data[0x52]
        r = data[0x53]

        argb = (a << 24) | (r << 16) | (g << 8) | b

        extruder_min_temp_c = binary.extract_uint16_le(data, 0x60)
        extruder_max_temp_c = binary.extract_uint16_le(data, 0x62)

        heated_bed_min_temp_c = binary.extract_uint16_le(data, 0x74)
        heated_bed_max_temp_c = binary.extract_uint16_le(data, 0x76)

        filament_diameter_mm = float(binary.extract_uint16_le(data, 0x78)) / 100.0
        filament_length_m = binary.extract_uint16_le(data, 0x7A)

        match filament_length_m:
            case 330:
                weight_grams = 1000
            case 247:
                weight_grams = 750
            case 198:
                weight_grams = 600
            case 165:
                weight_grams = 500
            case 82:
                weight_grams = 250
            case _:
                weight_grams = 1000  # Default to 1000g if unknown

        return GenericFilament(
            source_processor=self.name,
            unique_id=GenericFilament.generate_unique_id("Anycubic", sku, brand, filament_type, argb, filament_length_m),
            manufacturer=brand,
            type=filament_types[0] if filament_types else "PLA",
            modifiers=filament_types[1:],
            colors=[argb],
            diameter_mm=filament_diameter_mm,
            weight_grams=weight_grams,
            hotend_min_temp_c=extruder_min_temp_c,
            hotend_max_temp_c=extruder_max_temp_c,
            bed_temp_c=heated_bed_max_temp_c,
            drying_temp_c=0,
            drying_time_hours=0,
            manufacturing_date="0001-01-01"
        )