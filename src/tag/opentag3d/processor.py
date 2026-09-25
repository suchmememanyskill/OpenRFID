from filament import GenericFilament
from reader.scan_result import ScanResult
from tag.ndef_tag_processor import NdefRecord, NdefTagProcessor

from .schema import MIME_TYPE, SCHEMAS, decode_payload, version_number

# Based on: https://opentag3d.info/spec.html, using spec.json as a backbone to make future updates easier
# See "Reader Implementation Guidelines" for record selection and version handling.

class OpenTag3DTagProcessor(NdefTagProcessor):
    def __init__(self, config: dict):
        """Use the shared NDEF reader setup so this format works with existing configuration."""
        super().__init__(config)

    def process_ndef(self, scan_result: ScanResult, ndef_records: list[NdefRecord]) -> GenericFilament | None:
        """Find the OpenTag3D MIME record without claiming records belonging to other formats."""
        # The spec identifies tags by application/opentag3d, not by a fixed
        # position in the NDEF message. TNF 0x02 identifies a MIME record.
        # Return None on no match so the runtime can try another processor.
        for record in ndef_records:
            if record.tnf == 0x02 and record.mime_type == MIME_TYPE:
                filament = self.__parse_opentag3d_payload(scan_result, record.payload)
                if filament is not None:
                    return filament
        return None

    def __parse_opentag3d_payload(self, scan_result: ScanResult, payload: bytes) -> GenericFilament | None:
        """Select a compatible layout before decoding, and isolate failures to this record."""
        if payload is None or not isinstance(payload, (bytes, bytearray)):
            self.logger.error("OpenTag3D payload parsing failed: Invalid payload parameter")
            return None

        try:
            if len(payload) < 2:
                raise ValueError("Missing tag version")

            # Tag Version is an unsigned big-endian integer with three implied
            # decimal places: 2001 means 2.001. Read it before schema decoding;
            # a different major version may use completely different offsets.
            # Unlike missing trailing fields, a missing version cannot safely
            # be zero-filled because we do not yet know which layout to use.
            version = int.from_bytes(payload[:2], "big")
            schema = SCHEMAS.get(version // 1000)
            if schema is None:
                raise ValueError(f"Unsupported OpenTag3D major version: {version // 1000}")

            if version > version_number(schema["version"]):
                # Reader guidelines require attempting newer minor versions with
                # a warning. Unsupported majors are rejected above, including v1
                # until its separate memory map has been implemented.
                self.logger.warning(
                    "OpenTag3D version %d.%03d is newer than supported %s; attempting compatible decoding",
                    version // 1000, version % 1000, schema["version"]
                )

            data = decode_payload(payload, schema)
            return self.__to_filament(scan_result, data)
        except ValueError as e:
            self.logger.error("OpenTag3D payload parsing failed: %s", e)
            return None
        except Exception as e:
            self.logger.exception("OpenTag3D payload parsing failed: %s", e)
            return None

    def __to_filament(self, scan_result: ScanResult, data: dict) -> GenericFilament:
        """Adapt spec values to the existing shared model without changing other formats."""
        # Schema decoding already applied units. Only representation changes and
        # library defaults belong here; do not scale temperatures or diameter again.
        # Fields with no GenericFilament equivalent are deliberately not exported.
        colors = []
        for index in range(1, 5):
            r, g, b, a = data[f"color_{index}"]
            # The spec stores four RGBA colors and uses transparent black for
            # unused secondary colors. Keep the primary even if transparent,
            # and convert to the 0xAARRGGBB representation used by GenericFilament.
            if index == 1 or any((r, g, b, a)):
                colors.append((a << 24) | (r << 16) | (g << 8) | b)

        # GenericFilament has a range, but no target temperature. Use the target
        # for missing bounds without inventing material-specific temperatures.
        # This fallback is our adapter policy, not a rule imposed by the spec.
        hotend_min_temp_c = data["min_print_temp"] or data["print_temp"]
        hotend_max_temp_c = data["max_print_temp"] or data["print_temp"]
        if hotend_max_temp_c < hotend_min_temp_c:
            raise ValueError("Invalid print temperature range")

        return GenericFilament(
            source_processor=self.name,
            # Identify the physical tag; the spec's serial can be a shared batch ID.
            unique_id=GenericFilament.generate_unique_id("OpenTag3D", scan_result.uid.hex()),
            manufacturer=data["manufacturer"],
            type=data["material"],
            # Keep the spec's free-text modifier intact. GenericFilament handles
            # its existing CF/GF normalization and supported-material validation.
            modifiers=[data["material_mod"]] if data["material_mod"] else [],
            colors=colors,
            diameter_mm=data["diameter"],
            # Target Weight excludes the spool and is not measured/remaining weight.
            weight_grams=data["weight"],
            hotend_min_temp_c=hotend_min_temp_c,
            hotend_max_temp_c=hotend_max_temp_c,
            bed_temp_c=data["bed_temp"] or data["min_bed_temp"] or data["max_bed_temp"],
            drying_temp_c=data["max_dry_temp"],
            drying_time_hours=data["dry_time"],
            # Reuse the other processors' unknown-date sentinel for absent dates.
            manufacturing_date=data["mfg_date"] or "0001-01-01",
            td=data["td"],
        )
