from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.mifare_classic_tag_processor import MifareClassicTagProcessor, TagAuthentication
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from tag.tag_types import TagType
from . import constants as Constants
import struct
import tag.binary as binary

class BambuTagProcessor(MifareClassicTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

        self.key = self.load_hex_key_from_config(Constants.BAMBU_SALT_HASH) or b''
        self.enabled = len(self.key) > 0

        if not self.enabled:
            self.logger.warning("BambuTagProcessor: no valid key found in config, processor will be disabled")

    def authenticate_tag(self, scan_result : ScanResult) -> TagAuthentication | None:
        if not self.enabled:
            return None

        if scan_result.tag_type != TagType.MifareClassic1k:
            raise ValueError("BambuTagProcessor can only authenticate Mifare Classic 1K tags")
        
        return self.__hkdf_create_key(scan_result.uid)

    def process_tag(self, scan_result: ScanResult, data: bytes) -> GenericFilament | None:
        if not self.enabled:
            return None

        if scan_result.tag_type != TagType.MifareClassic1k or len(data) != Constants.TAG_TOTAL_SIZE:
            raise ValueError("BambuTagProcessor can only process Mifare Classic 1K tags")
        
        # https://github.com/Bambu-Research-Group/RFID-Tag-Guide/blob/main/BambuLabRfid.md
        # Extract filament type (Block 2)
        filament_type = binary.extract_string(data, Constants.FILAMENT_TYPE_POS, Constants.FILAMENT_TYPE_LEN)
        
        # Extract detailed filament type (Block 4)
        detailed_type = binary.extract_string(data, Constants.DETAILED_FILAMENT_TYPE_POS, Constants.DETAILED_FILAMENT_TYPE_LEN)
        
        # Extract material IDs (Block 1)
        material_variant_id = binary.extract_string(data, Constants.MATERIAL_VARIANT_ID_POS, Constants.MATERIAL_VARIANT_ID_LEN)
        material_id = binary.extract_string(data, Constants.MATERIAL_ID_POS, Constants.MATERIAL_ID_LEN)
        
        # Extract color (Block 5) - RGBA format
        r = data[Constants.COLOR_RGBA_POS]
        g = data[Constants.COLOR_RGBA_POS + 1]
        b = data[Constants.COLOR_RGBA_POS + 2]
        a = data[Constants.COLOR_RGBA_POS + 3]
        argb_color = (a << 24) | (r << 16) | (g << 8) | b
        
        # Extract spool weight (Block 5) - uint16 LE in grams
        weight_grams = binary.extract_uint16_le(data, Constants.SPOOL_WEIGHT_POS)
        
        # Extract filament diameter (Block 5) - float LE in mm
        diameter_mm = binary.extract_float_le(data, Constants.FILAMENT_DIAMETER_POS)
        
        # Extract temperatures and drying info (Block 6)
        drying_temp = binary.extract_uint16_le(data, Constants.DRYING_TEMP_POS)
        drying_time = binary.extract_uint16_le(data, Constants.DRYING_TIME_POS)
        bed_temp_type = binary.extract_uint16_le(data, Constants.BED_TEMP_TYPE_POS)
        bed_temp = binary.extract_uint16_le(data, Constants.BED_TEMP_POS)
        hotend_max_temp = binary.extract_uint16_le(data, Constants.HOTEND_MAX_TEMP_POS)
        hotend_min_temp = binary.extract_uint16_le(data, Constants.HOTEND_MIN_TEMP_POS)
        
        # Extract tray UID (Block 9)
        tray_uid = data[Constants.TRAY_UID_POS:Constants.TRAY_UID_POS+Constants.TRAY_UID_LEN]
        
        # Extract production date/time (Block 12)
        production_datetime = binary.extract_string(data, Constants.PRODUCTION_DATETIME_POS, Constants.PRODUCTION_DATETIME_LEN)
        
        # Extract extra color info (Block 16)
        format_identifier = binary.extract_uint16_le(data, Constants.FORMAT_IDENTIFIER_POS)
        color_count = binary.extract_uint16_le(data, Constants.COLOR_COUNT_POS)
        
        # Build colors list
        colors = [argb_color]
        if format_identifier == Constants.FORMAT_COLOR_INFO and color_count > 1:
            # Extract second color (ABGR format - reverse of ARGB)
            second_color_abgr = binary.extract_uint32_le(data, Constants.SECOND_COLOR_POS)
            # Convert ABGR to ARGB
            a2 = (second_color_abgr >> 24) & 0xFF
            b2 = (second_color_abgr >> 16) & 0xFF
            g2 = (second_color_abgr >> 8) & 0xFF
            r2 = second_color_abgr & 0xFF
            argb_color2 = (a2 << 24) | (r2 << 16) | (g2 << 8) | b2
            colors.append(argb_color2)
        
        # Parse production date from format: YYYY_MM_DD_HH_MM
        manufacturing_date = self.__parse_production_date(production_datetime)

        filament_modifier = detailed_type[len(filament_type):].strip() if detailed_type.startswith(filament_type) else detailed_type
        
        self.logger.debug("Found Bambu Lab filament tag:")
        self.logger.debug(" Filament Type: %s", filament_type)
        self.logger.debug(" Detailed Type: %s", detailed_type)
        self.logger.debug(" Filament Modifier: %s", filament_modifier)
        self.logger.debug(" Material Variant ID: %s", material_variant_id)
        self.logger.debug(" Material ID: %s", material_id)
        self.logger.debug(" Color (ARGB): 0x%08X", argb_color)
        self.logger.debug(" Weight (grams): %d", weight_grams)
        self.logger.debug(" Diameter (mm): %.2f", diameter_mm)
        self.logger.debug(" Drying Temp (C): %d", drying_temp)
        self.logger.debug(" Drying Time (hours): %d", drying_time)
        self.logger.debug(" Bed Temp Type: %d", bed_temp_type)
        self.logger.debug(" Bed Temp (C): %d", bed_temp)
        self.logger.debug(" Hotend Max Temp (C): %d", hotend_max_temp)
        self.logger.debug(" Hotend Min Temp (C): %d", hotend_min_temp)
        self.logger.debug(" Tray UID: %s", tray_uid.hex(":").upper())
        self.logger.debug(" Production Date/Time: %s", production_datetime)
        self.logger.debug(" Manufacturing Date: %s", manufacturing_date)
        self.logger.debug(" Color Count: %d", color_count)
        
        return GenericFilament(
            source_processor=self.name,
            unique_id=GenericFilament.generate_unique_id("Bambu Lab", filament_type, detailed_type, argb_color, production_datetime),
            manufacturer="Bambu",
            type=filament_type,
            modifiers=[filament_modifier] if len(filament_modifier) > 0 and filament_modifier != filament_type else [],
            colors=colors,
            diameter_mm=diameter_mm,
            weight_grams=weight_grams,
            hotend_min_temp_c=hotend_min_temp,
            hotend_max_temp_c=hotend_max_temp,
            bed_temp_c=bed_temp,
            drying_temp_c=drying_temp,
            drying_time_hours=drying_time,
            manufacturing_date=manufacturing_date
        )

    def __hkdf_create_key(self, uid : bytes) -> TagAuthentication:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=6 * 16,
            salt=self.key,
            info=b"RFID-A\0",
        )

        okm = hkdf.derive(uid)

        return TagAuthentication(
            [list(okm[i*6:(i+1)*6]) for i in range(16)],
            [[0x00] * 6 for _ in range(16)]
        )
    
    def __parse_production_date(self, date_str: str) -> str:
        """Parse production date from format YYYY_MM_DD_HH_MM to ISO 8601."""
        try:
            parts = date_str.split('_')
            if len(parts) >= 3:
                year = parts[0]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                return f"{year}-{month}-{day}"
        except:
            pass
        return "1970-01-01"  # Default fallback date