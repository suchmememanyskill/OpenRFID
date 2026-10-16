"""OpenSpool alpha: JSON numbers are decimal, strings are hex, invalid values are opaque."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reader.scan_result import ScanResult
from tag.openspool.processor import OpenspoolTagProcessor
from tag.tag_types import TagType


@pytest.fixture
def processor():
    return OpenspoolTagProcessor({"__name": "openspool"})


@pytest.fixture
def scan():
    return ScanResult(TagType.MifareUltralight, b"\x01\x02\x03\x04", b"\x00\x44", b"\x00", b"\x00")


def tag(data):
    # Single application/json NDEF record in a Type 2 tag image
    payload = json.dumps(data).encode()
    mime = b"application/json"
    record = bytes([0xD2, len(mime), len(payload)]) + mime + payload
    return bytes(12) + bytes.fromhex("e1103e00") + b"\x03" + bytes([len(record)]) + record + b"\xfe"


def spool(**extra):
    return {"protocol": "openspool", "version": "1.0", "type": "PLA", "color_hex": "FF0000",
            "min_temp": 190, "max_temp": 220, **extra}


@pytest.mark.parametrize("alpha, expected", [
    # JSON numbers: decimal, as in the U1 extended firmware's OpenSpool format
    (255, 0xFF),
    (128, 0x80),
    (0, 0x00),
    (80, 80),
    (127.6, 127),
    (300, 0xFF),
    (-5, 0x00),
    # Strings: hex, as before
    ("FF", 0xFF),
    ("80", 0x80),
    ("c0", 0xC0),
    ("#40", 0x40),
    ("0", 0x00),
])
def test_alpha_number_is_decimal_string_is_hex(processor, scan, alpha, expected):
    result = processor.process_tag(scan, tag(spool(alpha=alpha)))
    assert result is not None
    assert result.colors[0] == (expected << 24) | 0xFF0000
    assert result.to_dict()["alpha"] == expected


def test_missing_alpha_is_opaque(processor, scan):
    result = processor.process_tag(scan, tag(spool()))
    assert result.colors[0] == 0xFFFF0000


@pytest.mark.parametrize("alpha", ["zz", "", None, True, [128], {"a": 1}])
def test_invalid_alpha_is_opaque_and_tag_still_reads(processor, scan, alpha):
    # Previously any non-hex-string alpha made the whole tag unreadable
    result = processor.process_tag(scan, tag(spool(alpha=alpha)))
    assert result is not None
    assert result.type == "PLA"
    assert result.colors[0] == 0xFFFF0000
