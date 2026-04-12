from filament.generic import GenericFilament
from reader.scan_result import ScanResult
from tag.mifare_classic_tag_processor import MifareClassicTagProcessor, TagAuthentication
from tag.tag_types import TagType
import logging
from .constants import MATERIALS, COLORS

class QidiTagProcessor(MifareClassicTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

        # https://github.com/TinkerBarn/BoxRFID/blob/main/Phyton/source/box-rfid-V1.0.py#L101 also refers to another key, but lets just use the one key for now since it seems to work for some tags and I don't have any tags that require the other key to test with
        self.default_key = [[0xFF] * 6 for _ in range(16)]

    def authenticate_tag(self, scan_result: ScanResult) -> TagAuthentication | None:
        if not self.enabled:
            return None

        return TagAuthentication(
            self.default_key,
            self.default_key
        )
    
    def process_tag(self, scan_result: ScanResult, data: bytes) -> GenericFilament | None:
        if not self.enabled:
            return None
        
        if scan_result.tag_type != TagType.MifareClassic1k:
            raise ValueError("CrealityTagProcessor can only process Mifare Classic 1K tags")
        
        sector_one = data[64:112]
        material_code = sector_one[0]
        color_code = sector_one[1]
        manufacturer_code = sector_one[2]
        remaining = sector_one[3:]

        if remaining != bytes([0x00] * len(remaining)) or material_code == 0x00 or color_code == 0x00 or manufacturer_code == 0x00:
            logging.warning("Data format does not match expected QIDI format, skipping tag")
            logging.debug(f"Material code: {material_code}, Color code: {color_code}, Manufacturer code: {manufacturer_code}, Remaining: {remaining}")
            return None # Not a qidi tag
        
        if material_code not in MATERIALS:
            self.logger.error(f"Unknown material code {material_code} in QIDI tag")
            return None
        
        if color_code not in COLORS:
            self.logger.error(f"Unknown color code {color_code} in QIDI tag")
            return None
    
        material = MATERIALS[material_code]
        color = COLORS[color_code]
        type = material["type"]
        modifiers = material["modifiers"]

        return GenericFilament(
            source_processor=self.name,
            unique_id=GenericFilament.generate_unique_id("QIDI", material_code, color_code, manufacturer_code),
            manufacturer="QIDI",
            type=type,
            modifiers=modifiers,
            colors=[color],
            diameter_mm=1.75,
            weight_grams=1000,
            hotend_min_temp_c=0,
            hotend_max_temp_c=0,
            bed_temp_c=0,
            drying_temp_c=0,
            drying_time_hours=0,
            manufacturing_date="0001-01-01"
        )