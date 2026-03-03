from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.mifare_ultralight_tag_processor import MifareUltralightTagProcessor
from tag.tag_types import TagType
import tag.binary as binary
from . import constants as Constants

class ElegooTagProcessor(MifareUltralightTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

    def process_tag(self, scan_result: ScanResult, data: bytes) -> GenericFilament | None:
        if scan_result.tag_type != TagType.MifareUltralight:
            raise ValueError("AnycubicTagProcessor can only process Mifare Ultralight tags")
        
        filament_data = data[0x40:0x69]
        if filament_data[0x1:0x5] != b'\xEE\xEE\xEE\xEE':
            return None
        
        material_id = filament_data[0x08:0x0C]
        material_type = [chr(int(hex(x)[2:], 10)) for x in material_id if x != 0]

        material_subtype = binary.extract_uint16_be(filament_data, 0x0C)
        material = Constants.get_elegoo_material(material_subtype >> 8, material_subtype & 0xFF)

        if material is None:
            self.logger.warning(f"ElegooTagProcessor: Unknown material subtype {material_subtype:04X}")
            return None
        
        r = filament_data[0x10]
        g = filament_data[0x11]
        b = filament_data[0x12]
        a = filament_data[0x13]

        argb = (a << 24) | (r << 16) | (g << 8) | b

        min_temp = binary.extract_uint16_be(filament_data, 0x14)
        max_temp = binary.extract_uint16_be(filament_data, 0x16)

        diameter = binary.extract_uint16_be(filament_data, 0x1C) / 100.0
        weight_grams = binary.extract_uint16_be(filament_data, 0x1E)

        # Supposedly there's a date in there somewhere too, but that's still a mystery how to decode.

        return GenericFilament(
            source_processor=self.name,
            unique_id=GenericFilament.generate_unique_id("Elegoo", material_type, material_subtype, argb, diameter, weight_grams),
            manufacturer="Elegoo",
            type=material.material_type,
            modifiers=material.material_modifier,
            colors=[argb],
            diameter_mm=diameter,
            weight_grams=weight_grams,
            hotend_min_temp_c=min_temp,
            hotend_max_temp_c=max_temp,
            bed_temp_c=0, # TODO: Fix. Possibly create an internal registry of types for this.
            drying_temp_c=0,
            drying_time_hours=0,
            manufacturing_date="0001-01-01"
        )