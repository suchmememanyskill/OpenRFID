from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.ndef_tag_processor import NdefRecord, NdefTagProcessor
import urllib.parse

from . import constants as Constants


NDEF_URI_PREFIX_MAP = {
    0x00: "",
    0x01: "http://www.",
    0x02: "https://www.",
    0x03: "http://",
    0x04: "https://",
    0x05: "tel:",
    0x06: "mailto:",
    0x07: "ftp://anonymous:anonymous@",
    0x08: "ftp://ftp.",
    0x09: "ftps://",
    0x0A: "sftp://",
    0x0B: "smb://",
    0x0C: "nfs://",
    0x0D: "ftp://",
    0x0E: "dav://",
    0x0F: "news:",
    0x10: "telnet://",
    0x11: "imap:",
    0x12: "rtsp://",
    0x13: "urn:",
    0x14: "pop:",
    0x15: "sip:",
    0x16: "sips:",
    0x17: "tftp:",
    0x18: "btspp://",
    0x19: "btl2cap://",
    0x1A: "btgoep://",
    0x1B: "tcpobex://",
    0x1C: "irdaobex://",
    0x1D: "file://",
    0x1E: "urn:epc:id:",
    0x1F: "urn:epc:tag:",
    0x20: "urn:epc:pat:",
    0x21: "urn:epc:raw:",
    0x22: "urn:epc:",
    0x23: "urn:nfc:",
}


class SpooleaseTagProcessor(NdefTagProcessor):
    def __init__(self, config: dict):
        super().__init__(config)

    def process_ndef(self, scan_result: ScanResult, ndef_records: list[NdefRecord]) -> GenericFilament | None:
        for record in ndef_records:
            if record.tnf == 0x01 and record.type == "U":
                filament = self.__parse_spoolease_payload(record.payload)
                if filament is not None:
                    return filament

        self.logger.error("SpoolEase processing failed: No valid SpoolEase NDEF URI record found")
        return None

    def __parse_spoolease_payload(self, payload: bytes) -> GenericFilament | None:
        if payload is None or not isinstance(payload, (bytes, bytearray)):
            self.logger.error("SpoolEase payload parsing failed: Invalid payload parameter")
            return None

        try:
            url = self.__decode_uri_payload(payload)
            parsed = urllib.parse.urlparse(url)

            if parsed.netloc.lower() != "tag.spoolease.io" or not parsed.path.startswith("/S1"):
                self.logger.error("SpoolEase payload parsing failed: Unsupported URL '%s'", url)
                return None

            query = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)

            raw_material = (query.get("M", ["PLA"])[0] or "PLA").upper()
            material = Constants.FILAMENT_TYPE_ALIASES.get(raw_material, raw_material)
            subtype = query.get("MS", [""])[0] or ""
            brand = query.get("B", ["Generic"])[0] or "Generic"
            color_field = query.get("CC", ["FFFFFFFF"])[0] or "FFFFFFFF"

            hotend_min_temp_c = self.__parse_required_int(query, "NN")
            hotend_max_temp_c = self.__parse_required_int(query, "NX")
            weight_grams = self.__parse_optional_int(query, "WL", 1000)

            if hotend_max_temp_c < hotend_min_temp_c:
                self.logger.error("SpoolEase payload parsing failed: Invalid temperature values")
                return None

            colors = self.__parse_colors(color_field)
            extra_data = Constants.FILAMENT_TYPE_TO_EXTENDED_DATA.get(material)

            bed_temp_c = extra_data.bed_temp_c if extra_data is not None else 0.0
            drying_temp_c = extra_data.drying_temp_c if extra_data is not None else 0.0
            drying_time_hours = extra_data.drying_time_hours if extra_data is not None else 0.0

            return GenericFilament(
                source_processor=self.name,
                unique_id=GenericFilament.generate_unique_id("SpoolEase", brand, material, subtype, *colors, weight_grams),
                manufacturer=brand,
                type=material,
                modifiers=[subtype] if subtype else [],
                colors=colors,
                diameter_mm=1.75,
                weight_grams=weight_grams,
                hotend_min_temp_c=hotend_min_temp_c,
                hotend_max_temp_c=hotend_max_temp_c,
                bed_temp_c=bed_temp_c,
                drying_temp_c=drying_temp_c,
                drying_time_hours=drying_time_hours,
                manufacturing_date="0001-01-01",
            )
        except ValueError as e:
            self.logger.error("SpoolEase payload parsing failed: %s", e)
            return None
        except Exception as e:
            self.logger.exception("SpoolEase payload parsing failed: %s", e)
            return None

    def __decode_uri_payload(self, payload: bytes) -> str:
        if len(payload) < 1:
            raise ValueError("Invalid NDEF URI payload")

        prefix = NDEF_URI_PREFIX_MAP.get(payload[0], "")
        suffix = payload[1:].decode("utf-8", errors="ignore")
        return (prefix + suffix).strip()

    def __parse_required_int(self, query: dict[str, list[str]], key: str) -> int:
        values = query.get(key)
        if not values or values[0] == "":
            raise ValueError(f"Missing required field '{key}'")
        return int(values[0])

    def __parse_optional_int(self, query: dict[str, list[str]], key: str, default: int) -> int:
        values = query.get(key)
        if not values or values[0] == "":
            return default
        return int(values[0])

    def __parse_colors(self, color_field: str) -> list[int]:
        colors = []
        alpha = 0xFF

        for i, color_code in enumerate(color_field.split(";")):
            if len(colors) >= 5:
                break

            color_code = color_code.strip()
            if not color_code:
                continue

            rgb, parsed_alpha = self.__parse_rgba_hex(color_code)
            colors.append((parsed_alpha << 24) | rgb)

            if i == 0:
                alpha = parsed_alpha

        if not colors:
            colors = [(alpha << 24) | 0xFFFFFF]

        return colors

    def __parse_rgba_hex(self, value: str) -> tuple[int, int]:
        hex_str = str(value).strip()
        if hex_str.startswith("#"):
            hex_str = hex_str[1:]

        if len(hex_str) == 6:
            return int(hex_str, 16), 0xFF
        if len(hex_str) == 8:
            return int(hex_str[:6], 16), int(hex_str[6:], 16)

        raise ValueError(f"Unsupported RGBA hex length: {len(hex_str)}")
