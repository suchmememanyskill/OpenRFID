from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.tag_types import TagType
from tag.mifare_classic_tag_processor import MifareClassicTagProcessor, TagAuthentication
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from . import constants as Constants

class CrealityTagProcessor(MifareClassicTagProcessor):
    def __init__(self, config : dict):
        super().__init__(config)

        self.key = self.load_hex_key_from_config(Constants.CREALITY_SALT_HASH) or b''
        self.enabled = len(self.key) > 0

        if not self.enabled:
            logging.warning("CrealityTagProcessor: no valid key found in config, processor will be disabled")

        self.encryption_key = self.load_hex_key_from_config(Constants.CREALITY_ENCRYPTION_KEY_HASH, "encryption_key")

        if self.encryption_key is None:
            logging.warning("No valid encryption key found in config for CrealityTagProcessor, will attempt to process tags without decryption")

    def authenticate_tag(self, scan_result) -> TagAuthentication | None:
        if not self.enabled:
            return None

        if scan_result.tag_type != TagType.MifareClassic1k:
            raise ValueError("CrealityTagProcessor can only authenticate Mifare Classic 1K tags")

        return self.__hkdf_create_key(scan_result.uid)
    
    def process_tag(self, scan_result: ScanResult, data: bytes) -> GenericFilament | None:
        if not self.enabled:
            return None

        if scan_result.tag_type != TagType.MifareClassic1k:
            raise ValueError("CrealityTagProcessor can only process Mifare Classic 1K tags")
        
        data_subset = data[64:64+48]

        test1 = data_subset[3]
        test2 = data_subset[17]

        is_encrypted = not (test1 == 0x32 and test2 in [0x30, 0x23])

        if is_encrypted:
            if self.encryption_key is None:
                logging.warning("Tag data appears to be encrypted but no valid encryption key is configured for CrealityTagProcessor")
                return None

            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.ECB(),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            data_subset = decryptor.update(data_subset) + decryptor.finalize()

        data_str = data_subset.decode('ascii', errors='ignore')

        # TODO: Put all constants in constants.py
        batch = data_str[0:3]
        year = 2000 + int(data_str[3:5])
        month = int(data_str[5], 16)
        day = int(data_str[6:8])
        supplier = data_str[8:12]
        material = data_str[12:17]
        color_prefix = data_str[17] # '0' or '#'
        color = (0xFF << 24) | int(data_str[18:24], 16)
        length_m = int(data_str[24:28])
        serial = data_str[28:34]
        reserve = data_str[34:48]

        logging.debug("Found Creality filament tag:")
        logging.debug(" Batch: %s", batch)
        logging.debug(" Date: %04d-%02d-%02d", year, month, day)
        logging.debug(" Supplier: %s", supplier)
        logging.debug(" Material: %s", material)
        logging.debug(" Color: %s%X", color_prefix, color)
        logging.debug(" Length (m): %d", length_m)
        logging.debug(" Serial: %s", serial)
        logging.debug(" Reserve: %s", reserve)
        
        match length_m:
            case 330:
                weight_grams = 1000
            case 165:
                weight_grams = 500
            case 80:
                weight_grams = 250
            case _:
                weight_grams = 1000  # Default to 1000g if unknown

        if material not in Constants.CREALITY_FILAMENT_CODE_TO_DATA:
            logging.error("Unknown Creality filament material code: %s", material)
            return None

        extra_data = Constants.CREALITY_FILAMENT_CODE_TO_DATA[material]

        return GenericFilament(
            source_processor=self.name,
            unique_id=GenericFilament.generate_unique_id("Creality", data_str),
            manufacturer="Creality",
            type=extra_data.type,
            modifiers=extra_data.modifiers,
            colors=[color],
            diameter_mm=1.75,
            weight_grams=weight_grams,
            hotend_min_temp_c=extra_data.hotend_min_temp_c,
            hotend_max_temp_c=extra_data.hotend_max_temp_c,
            bed_temp_c=extra_data.bed_temp_c,
            drying_temp_c=extra_data.drying_temp_c,
            drying_time_hours=extra_data.drying_time_hours,
            manufacturing_date=f"{year:04d}-{month:02d}-{day:02d}"
        )
    
    def __hkdf_create_key(self, uid: bytes) -> TagAuthentication:
        if len(uid) != 4:
            raise ValueError("UID must be 4 bytes for CrealityTagProcessor")

        plaintext = uid + uid + uid + uid
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.ECB(),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        derived_key = ciphertext[:6]
        
        keys_a = [[0xFF] * 6 for _ in range(16)]  # Default keys
        keys_b = [[0xFF] * 6 for _ in range(16)]  # Default keys
        
        keys_a[1] = list(derived_key)
        
        return TagAuthentication(keys_a, keys_b)