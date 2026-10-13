"""Regenerate the synthetic TigerTag fixture used to test new field parsing.

Run from the repo root:

    python test/scripts/build_tigertag_fixture.py

The script writes a deterministic NTAG-style binary into
``test/tags/Tigertag/New Fields TigerTag.bin`` and the matching
expected-output YAML alongside it. The parametrised test in
``test/test_tags.py`` discovers the pair automatically.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tag.tigertag import constants as Constants  # noqa: E402

FIXTURE_DIR = ROOT / "test" / "tags" / "Tigertag"
FIXTURE_NAME = "New Fields TigerTag"
MESSAGE = "Galaxy Black"
MANUFACTURER_NAME = "Sunlu"
MANUFACTURER_ID = 51857  # "Sunlu" in the bundled brand registry

# NTAG-style fixture: the parser strips USER_DATA_BYTE_OFFSET (16) bytes of
# header before reading. We only need a 96-byte user-data region for parsing,
# but pad to the same 540 byte size as the real fixtures so anything that
# grows the prefix in future keeps working.
HEADER_LEN = Constants.USER_DATA_BYTE_OFFSET
TOTAL_LEN = 540


def build_user_data() -> bytes:
    buf = bytearray(96)
    # OFF_TAG_ID — must be one of TIGERTAG_VALID_DATA_IDS
    struct.pack_into(">I", buf, Constants.OFF_TAG_ID, 0x5BF59264)
    # OFF_PRODUCT_ID
    struct.pack_into(">I", buf, Constants.OFF_PRODUCT_ID, 0x00000001)
    # OFF_MATERIAL_ID = 38219 ("PLA" in the bundled registry).
    struct.pack_into(">H", buf, Constants.OFF_MATERIAL_ID, 38219)
    # OFF_BRAND_ID = Sunlu (so manufacturer renders as a real name).
    struct.pack_into(">H", buf, Constants.OFF_BRAND_ID, MANUFACTURER_ID)
    # IDs left at 0 → registry resolves them as "Unknown(0)".
    # OFF_COLOR_RGBA = pure black, opaque
    buf[Constants.OFF_COLOR_RGBA + 0] = 0x00
    buf[Constants.OFF_COLOR_RGBA + 1] = 0x00
    buf[Constants.OFF_COLOR_RGBA + 2] = 0x00
    buf[Constants.OFF_COLOR_RGBA + 3] = 0xFF
    # OFF_WEIGHT (3 bytes BE) = 1000
    weight = 1000
    buf[Constants.OFF_WEIGHT + 0] = (weight >> 16) & 0xFF
    buf[Constants.OFF_WEIGHT + 1] = (weight >> 8) & 0xFF
    buf[Constants.OFF_WEIGHT + 2] = weight & 0xFF
    # Hotend temps
    struct.pack_into(">H", buf, Constants.OFF_TEMP_MIN, 230)
    struct.pack_into(">H", buf, Constants.OFF_TEMP_MAX, 190)
    # Bed temps
    buf[Constants.OFF_BED_TEMP_MIN] = 50
    buf[Constants.OFF_BED_TEMP_MAX] = 60
    # Drying
    buf[Constants.OFF_DRY_TEMP] = 45
    buf[Constants.OFF_DRY_TIME] = 8
    # Timestamp = 2025-01-01 00:00:00 UTC, encoded as seconds since the
    # TigerTag epoch (2000-01-01 UTC). 1735689600 - 946684800 = 789004800.
    struct.pack_into(">I", buf, Constants.OFF_TIMESTAMP, 789004800)
    # TD = 0.8 mm → raw 8
    struct.pack_into(">H", buf, Constants.OFF_TD, 8)
    # Custom message — written at OFF_METADATA (byte 48), capped at MESSAGE_LENGTH.
    encoded = MESSAGE.encode("utf-8")[: Constants.MESSAGE_LENGTH]
    buf[Constants.OFF_METADATA : Constants.OFF_METADATA + len(encoded)] = encoded
    return bytes(buf)


def build_binary() -> bytes:
    user = build_user_data()
    out = bytearray(TOTAL_LEN)
    # Header bytes are not parsed, but mimic real NTAG dumps with a UID block.
    out[0:9] = b"\x04\xde\xad\xbe\xef\xca\xfe\x00\x00"
    out[HEADER_LEN : HEADER_LEN + len(user)] = user
    return bytes(out)


def expected_yaml() -> dict:
    # Mirrors the subset checked by test_tag_processor_fixture_matches_expected_output.
    return {
        "bed_temp_c": 50.0,
        "bed_temp_max_c": 60.0,
        # Rendered as a 0xAARRGGBB hex literal (see HexIntDumper) so the file
        # reads the same way as the other Tigertag fixtures.
        "colors": [0xFF000000],
        "diameter_mm": 1.75,
        "drying_temp_c": 45.0,
        "drying_time_hours": 8.0,
        "hotend_max_temp_c": 190.0,
        "hotend_min_temp_c": 230.0,
        "manufacturer": MANUFACTURER_NAME,
        "manufacturing_date": "2025-01-01",
        "message": MESSAGE,
        "source_processor": "TigerTagProcessor",
        "td": 0.8,
        "type": "PLA",
        "weight_grams": 1000.0,
    }


class HexIntDumper(yaml.SafeDumper):
    """yaml.SafeDumper variant that renders ints as 0x... hex literals.

    The other Tigertag fixtures store ARGB colors as ``0xFFRRGGBB``; matching
    their style keeps diffs and grep results readable.
    """


def _represent_int_as_hex(dumper: yaml.SafeDumper, value: int) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:int", f"0x{value:X}")


HexIntDumper.add_representer(int, _represent_int_as_hex)


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    bin_path = FIXTURE_DIR / f"{FIXTURE_NAME}.bin"
    yml_path = FIXTURE_DIR / f"{FIXTURE_NAME}.yml"

    bin_path.write_bytes(build_binary())
    with yml_path.open("w", encoding="utf-8") as fh:
        yaml.dump(expected_yaml(), fh, Dumper=HexIntDumper, sort_keys=True)

    print(f"Wrote {bin_path} ({bin_path.stat().st_size} bytes)")
    print(f"Wrote {yml_path}")


if __name__ == "__main__":
    main()
