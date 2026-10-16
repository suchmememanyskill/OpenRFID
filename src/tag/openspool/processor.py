from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.ndef_tag_processor import NdefRecord, NdefTagProcessor
import json
from . import constants as Constants

# Adapted from https://github.com/paxx12/SnapmakerU1-Extended-Firmware/blob/3c97d1d80309d817ad37f2daac8e436712cc7865/overlays/firmware-extended/13-rfid-support/root/home/lava/klipper/klippy/extras/filament_protocol_ndef.py

class OpenspoolTagProcessor(NdefTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

    def process_ndef(self, scan_result: ScanResult, ndef_records: list[NdefRecord]) -> GenericFilament | None:
        for record in ndef_records:
            if record.mime_type == "application/json":
                parse = self.__openspool_parse_payload(record.payload)

                if parse is not None:
                    return parse
        
        self.logger.error("OpenSpool processing failed: No valid OpenSpool NDEF record found")
        return None

    def __openspool_parse_payload(self, payload : bytes) -> GenericFilament | None:
        if None == payload or not isinstance(payload, (bytes, bytearray)):
            self.logger.error("OpenSpool payload parsing failed: Invalid payload parameter")
            return None

        try:
            payload_str = payload.decode('utf-8')
            self.logger.debug(f"OpenSpool JSON payload: {payload_str}")

            data = json.loads(payload_str)

            if not isinstance(data, dict):
                self.logger.error(f"OpenSpool payload parsing failed: JSON data is not a dict, got {type(data)}")
                return None

            if data.get('protocol') != 'openspool':
                self.logger.error(f"OpenSpool payload parsing failed: Invalid protocol '{data.get('protocol')}', expected 'openspool'")
                return None
            
            brand = data.get('brand', 'Generic')
            main_type = data.get('type', 'PLA').upper()
            subtype = data.get('subtype', '')
            color_hex = self.__parse_color_hex(data.get('color_hex', 'FFFFFF'))
            alpha = self.__parse_alpha(data.get('alpha', 'FF'))
            color_argb = (alpha << 24) | color_hex

            try:
                diameter_mm = float(data.get('diameter', 1.75))
            except (ValueError, TypeError):
                diameter_mm = 1.75

            try:
                weight_grams = int(data.get('weight', 1000))
            except (ValueError, TypeError):
                weight_grams = 1000

            min_temp = int(data.get('min_temp', 0))
            max_temp = int(data.get('max_temp', 0))

            if max_temp < min_temp:
                self.logger.error("OpenSpool payload parsing failed: Invalid temperature values")
                return None
            
            if main_type in Constants.FILAMENT_TYPE_TO_EXTENDED_DATA:
                extra_data = Constants.FILAMENT_TYPE_TO_EXTENDED_DATA[main_type]
                bed_temp_c = extra_data.bed_temp_c
                drying_temp_c = extra_data.drying_temp_c
                drying_time_hours = extra_data.drying_time_hours
            else:
                bed_temp_c = 0.0
                drying_temp_c = 0.0
                drying_time_hours = 0.0

            return GenericFilament(
                source_processor=self.name,
                unique_id=GenericFilament.generate_unique_id("OpenSpool", brand, main_type, subtype, color_argb),
                manufacturer=brand,
                type=main_type,
                modifiers=[subtype] if subtype else [],
                colors=[color_argb],
                diameter_mm=diameter_mm,
                weight_grams=weight_grams,
                hotend_min_temp_c=min_temp,
                hotend_max_temp_c=max_temp,
                bed_temp_c=bed_temp_c,
                drying_temp_c=drying_temp_c,
                drying_time_hours=drying_time_hours,
                manufacturing_date="0001-01-01"
            )
        except json.JSONDecodeError as e:
            self.logger.exception("OpenSpool payload parsing failed: Invalid JSON: %s", str(e))
            return None
        except Exception as e:
            self.logger.exception("OpenSpool payload parsing failed: %s", str(e))
            return None
    
    def __parse_alpha(self, value) -> int:
        # JSON numbers are decimal (e.g. 128), as documented for the Snapmaker U1
        # extended firmware and read by its built-in OpenSpool reader. Strings are
        # hex (e.g. "80"), as this processor has always read them. Invalid values
        # fall back to opaque instead of rejecting the whole tag.
        try:
            if isinstance(value, bool):
                raise TypeError("alpha must be a number or hex string")
            if isinstance(value, (int, float)):
                alpha = int(value)
            else:
                alpha_str = str(value).strip()
                if alpha_str.startswith('#'):
                    alpha_str = alpha_str[1:]
                alpha = int(alpha_str, 16)
            return max(0x00, min(0xFF, alpha))
        except (ValueError, TypeError, OverflowError):
            self.logger.warning(f"OpenSpool: Invalid alpha value {value!r}, using FF")
            return 0xFF

    def __parse_color_hex(self, value : str):
        try:
            hex_str = str(value)
            if hex_str.startswith('#'):
                hex_str = hex_str[1:]
            return int(hex_str, 16)
        except (ValueError, TypeError):
            return 0xFFFFFF