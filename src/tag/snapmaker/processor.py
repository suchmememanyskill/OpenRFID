from filament import GenericFilament
import hashlib, hmac
from reader.scan_result import ScanResult
from tag.mifare_classic_tag_processor import MifareClassicTagProcessor, TagAuthentication
from tag.tag_types import TagType
from . import constants as Constants
# Version 39.0.2 of cryptography
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

class SnapmakerTagProcessor(MifareClassicTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

        self.key : bytes = self.load_hex_key_from_config(Constants.SNAPMAKER_SALT_HASH) or b''
        self.enabled = len(self.key) > 0

        if not self.enabled:
            self.logger.warning("SnapmakerTagProcessor: no valid key found in config, processor will be disabled")

    def authenticate_tag(self, scan_result : ScanResult) -> TagAuthentication | None:
        if not self.enabled:
            return None

        if scan_result.tag_type != TagType.MifareClassic1k:
            raise ValueError("SnapmakerTagProcessor can only authenticate Mifare Classic 1K tags")
        
        ikm = scan_result.uid[0:4]
        
        return TagAuthentication(
            self.__hkdf_create_key(ikm, self.key[:25], 'a'),
            self.__hkdf_create_key(ikm, self.key, 'b')
        )

    def process_tag(self, scan_result : ScanResult, data : bytes) -> GenericFilament | None:
        if not self.enabled:
            return None

        if scan_result.tag_type != TagType.MifareClassic1k or len(data) != Constants.M1_PROTO_TOTAL_SIZE:
            raise ValueError("SnapmakerTagProcessor can only process Mifare Classic 1K tags")
        
        valid_signature, rsa_version = self.__verify_signature(data)

        if not valid_signature:
            return None
        
        version = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_VERSION_POS, Constants.M1_PROTO_VERSION_LEN))
        vendor = self.__slice(data, Constants.M1_PROTO_VENDOR_POS, Constants.M1_PROTO_VENDOR_LEN, False).decode('ascii').rstrip('\x00')
        manufacturer = self.__slice(data, Constants.M1_PROTO_MANUFACTURER_POS, Constants.M1_PROTO_MANUFACTURER_LEN, False).decode('ascii').rstrip('\x00')
        main_type_code = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_MAIN_TYPE_POS, Constants.M1_PROTO_MAIN_TYPE_LEN))
        
        if main_type_code not in Constants.FILAMENT_PROTO_MAIN_TYPE_MAPPING:
            self.logger.error("Unknown main type code: %d", main_type_code)
            return None
        
        main_type = Constants.FILAMENT_PROTO_MAIN_TYPE_MAPPING[main_type_code]
        sub_type_code = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_SUB_TYPE_POS, Constants.M1_PROTO_SUB_TYPE_LEN))

        if sub_type_code not in Constants.FILAMENT_PROTO_SUB_TYPE_MAPPING:
            self.logger.error("Unknown sub type code: %d", sub_type_code)
            return None
        
        sub_type = Constants.FILAMENT_PROTO_SUB_TYPE_MAPPING[sub_type_code]
        tray = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_TRAY_POS, Constants.M1_PROTO_TRAY_LEN))
        alpha = 0xFF - data[Constants.M1_PROTO_ALPHA_POS]

        color_nums = data[Constants.M1_PROTO_COLOR_NUMS_POS]

        if color_nums > Constants.FILAMENT_PROTO_COLOR_NUMS_MAX:
            self.logger.error("Invalid amount of colors: %d", color_nums)
            return None
        
        rgb_1 = (alpha << 24) | self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_RGB_1_POS, Constants.M1_PROTO_RGB_1_LEN, False))
        rgb_2 = (alpha << 24) | self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_RGB_2_POS, Constants.M1_PROTO_RGB_2_LEN, False))
        rgb_3 = (alpha << 24) | self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_RGB_3_POS, Constants.M1_PROTO_RGB_3_LEN, False))
        rgb_4 = (alpha << 24) | self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_RGB_4_POS, Constants.M1_PROTO_RGB_4_LEN, False))
        rgb_5 = (alpha << 24) | self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_RGB_5_POS, Constants.M1_PROTO_RGB_5_LEN, False))
        argb_color = (alpha << 24) | (rgb_1 & 0xFFFFFF)

        diameter_mm = float(self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_DIAMETER_POS, Constants.M1_PROTO_DIAMETER_LEN))) / 100.0
        weight_grams = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_WEIGHT_POS, Constants.M1_PROTO_WEIGHT_LEN))
        length_meters = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_LENGTH_POS, Constants.M1_PROTO_LENGTH_LEN))
        drying_temp = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_DRY_TEMP_POS, Constants.M1_PROTO_DRY_TEMP_LEN))
        drying_time = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_DRY_TIME_POS, Constants.M1_PROTO_DRY_TIME_LEN))
        hotend_max_temp = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_HOTEND_MAX_TEMP_POS, Constants.M1_PROTO_HOTEND_MAX_TEMP_LEN))
        hotend_min_temp = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_HOTEND_MIN_TEMP_POS, Constants.M1_PROTO_HOTEND_MIN_TEMP_LEN))
        bed_type = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_BED_TYPE_POS, Constants.M1_PROTO_BED_TYPE_LEN))
        bed_temp = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_BED_TEMP_POS, Constants.M1_PROTO_BED_TEMP_LEN))
        first_layer_temp = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_FIRST_LAYER_TEMP_POS, Constants.M1_PROTO_FIRST_LAYER_TEMP_LEN))
        other_layer_temp = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_OTHER_LAYER_TEMP_POS, Constants.M1_PROTO_OTHER_LAYER_TEMP_LEN))
        sku = self.__convert_to_int(self.__slice(data, Constants.M1_PROTO_SKU_POS, Constants.M1_PROTO_SKU_LEN))
        card_uid = self.__slice(data, Constants.M1_PROTO_UID_POS, Constants.M1_PROTO_UID_LEN, False)

        self.logger.debug("Found Snapmaker filament tag:")
        self.logger.debug(" RSA Key Version: %d", rsa_version)
        self.logger.debug(" Version: %d", version)
        self.logger.debug(" Vendor: %s", vendor)
        self.logger.debug(" Manufacturer: %s", manufacturer)
        self.logger.debug(" Main Type: %s", main_type)
        self.logger.debug(" Sub Type: %s", sub_type)
        self.logger.debug(" Tray: %d", tray)
        self.logger.debug(" Color Nums: %d", color_nums)
        self.logger.debug(" RGB1: 0x%08X", rgb_1)
        self.logger.debug(" RGB2: 0x%08X", rgb_2)
        self.logger.debug(" RGB3: 0x%08X", rgb_3)
        self.logger.debug(" RGB4: 0x%08X", rgb_4)
        self.logger.debug(" RGB5: 0x%08X", rgb_5)
        self.logger.debug(" ARGB Color: 0x%08X", argb_color)
        self.logger.debug(" Diameter (mm): %f", diameter_mm)
        self.logger.debug(" Weight (grams): %d", weight_grams)
        self.logger.debug(" Length (meters): %d", length_meters)
        self.logger.debug(" Drying Temp (C): %d", drying_temp)
        self.logger.debug(" Drying Time (hours): %d", drying_time)
        self.logger.debug(" Hotend Max Temp (C): %d", hotend_max_temp)
        self.logger.debug(" Hotend Min Temp (C): %d", hotend_min_temp)
        self.logger.debug(" Bed Type: %d", bed_type)
        self.logger.debug(" Bed Temp (C): %d", bed_temp)
        self.logger.debug(" First Layer Temp (C): %d", first_layer_temp)
        self.logger.debug(" Other Layer Temp (C): %d", other_layer_temp)
        self.logger.debug(" SKU: %d", sku)
        self.logger.debug(" Card UID: %s", card_uid.hex(':').upper())

        colors = [rgb_1, rgb_2, rgb_3, rgb_4, rgb_5][:color_nums]

        return GenericFilament(
            source_processor=self.name,
            unique_id=GenericFilament.generate_unique_id("Snapmaker", vendor, manufacturer, main_type, sub_type, argb_color, weight_grams, sku, tray),
            manufacturer=vendor,
            type=main_type,
            modifiers=[sub_type],
            colors=colors,
            diameter_mm=diameter_mm,
            weight_grams=weight_grams,
            hotend_min_temp_c=hotend_min_temp,
            hotend_max_temp_c=hotend_max_temp,
            bed_temp_c=bed_temp,
            drying_temp_c=drying_temp,
            drying_time_hours=drying_time,
            manufacturing_date="2026-01-01" # TODO: Extract actual date
        )
    
    def __hkdf_create_key(self, ikm : bytes, salt : bytes, key_type='a'):
        sector_count = 16
        key_len = 6
        hash_algo = hashlib.sha256

        if salt.endswith(b'\0'):
            salt = salt[:-1]

        keys = []
        prk = hmac.new(salt, ikm, hash_algo).digest()
        for i in range(sector_count):
            info = f"key_{key_type}_{i}".encode()
            okm = bytearray()
            counter = 1
            while len(okm) < key_len:
                data = hmac.new(prk, info + bytes([counter]), hash_algo).digest()
                okm.extend(data)
                counter += 1
            okm_list = [int(byte) for byte in okm[:key_len]]
            keys.append(okm_list)

        return keys
    
    def __verify_signature(self, data: bytes) -> tuple[bool, int]:
        rsa_ver = data[Constants.M1_PROTO_RSA_KEY_VER_POS : Constants.M1_PROTO_RSA_KEY_VER_POS + Constants.M1_PROTO_RSA_KEY_VER_LEN]
        rsa_ver = (rsa_ver[1] << 8) | (rsa_ver[0])

        public_key = Constants.FILAMENT_PROTO_RSA_PUBLIC_KEY_MAPPING.get(rsa_ver, None)
        if public_key is None:
            self.logger.error("Unknown RSA key version: %d", rsa_ver)
            return (False, rsa_ver)
        
        signature_read : bytes = b''
        for i in range(6):
            signature_read += data[(10 + i) * 64 : (10 + i) * 64 + 48]

        if not self.__verify_signature_pkcs1(public_key,
                             data[0:640], signature_read[0:256]):
            self.logger.error("Signature verification failed for RSA key version: %d", rsa_ver)
            return (False, rsa_ver)
        
        return (True, rsa_ver)

    def __verify_signature_pkcs1(self, public_key : bytes, data : bytes, signature : bytes) -> bool:
        try:
            pem = serialization.load_pem_public_key(public_key, backend=default_backend())
            pem.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        
    def __slice(self, data: bytes, start: int, length: int, reversed : bool = True) -> bytes:
        data = data[start:start+length]

        if reversed:
            data = data[::-1]

        return data

    def __convert_to_int(self, byte_data: bytes) -> int:
        result = 0
        for byte in byte_data:
            result = (result << 8) | byte
        return result