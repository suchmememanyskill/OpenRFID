"""Independent payload offsets exercise the bundled official schema and NDEF path."""
import copy
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reader.scan_result import ScanResult
from tag.opentag3d import OpenTag3DTagProcessor
from tag.opentag3d.schema import SCHEMAS, decode_payload

from tag.tag_types import TagType


@pytest.fixture
def processor():
    return OpenTag3DTagProcessor({"__name": "opentag3d"})


@pytest.fixture
def scan():
    return ScanResult(TagType.MifareUltralight, b"\x01\x02\x03\x04", b"\x00\x44", b"\x00", b"\x00")


@pytest.fixture
def payload():
    # Preserve the supplied capture's actual length, including its omitted tail.
    path = Path(__file__).parent / "tags/OpenTag3D/Polar Filament PLA Pure Light Blue.payload.hex"
    return bytearray.fromhex(path.read_text())


def record(payload, mime=b"application/opentag3d", long=False, flags=0xc0, identifier=b""):
    header = flags | 2 | (0 if long else 0x10) | (8 if identifier else 0)
    length = len(payload).to_bytes(4 if long else 1, "big")
    return bytes([header, len(mime)]) + length + (bytes([len(identifier)]) if identifier else b"") + mime + identifier + payload


def tag(message, padding=b""):
    length = bytes([len(message)]) if len(message) < 255 else b"\xff" + len(message).to_bytes(2, "big")
    return bytes.fromhex("e1103e00") + padding + b"\x03" + length + message + b"\xfe"


def test_fixture_payload_is_independent(payload):
    assert len(payload) == 216
    assert payload[:5] == b"\x07\xd0PLA"


def test_binary_fixture_wraps_captured_payload(payload):
    # Only framing and simulated system memory are generated. Assert the main
    # fixture suite receives exactly the captured payload, with its real length.
    path = Path(__file__).parent / "tags/OpenTag3D/Polar Filament PLA Pure Light Blue.bin"
    expected = bytes(12) + tag(record(payload))
    assert path.read_bytes() == expected.ljust(540, b"\x00")


def test_modified_payload_utf8_multicolor_and_td(processor, scan, payload):
    # Exercise fields the real single-color spool does not populate, while
    # leaving the saved fixture faithful to the captured payload.
    payload[12:28] = "Example Mfg Ω".encode().ljust(16, b"\x00")
    payload[60:76] = bytes.fromhex("ff804080 002244ff 00000000 00000000")
    payload[167] = 118
    result = processor.process_tag(scan, tag(record(payload)))
    assert result.manufacturer == "Example Mfg Ω"
    assert result.colors == [0x80ff8040, 0xff002244]
    assert result.td == pytest.approx(11.8)


@pytest.mark.parametrize("long", [False, True])
def test_multiple_records_and_identifier(processor, scan, payload, long):
    message = record(b"{}", b"application/json", flags=0x80)
    message += record(payload, long=long, flags=0x40, identifier=b"spool")
    result = processor.process_tag(scan, tag(message))
    assert result.manufacturer == "Polar Filament"
    assert result.colors == [0xff14addb]
    assert "metadata" not in result.to_dict()
    json.dumps(result.to_dict())


@pytest.mark.parametrize("version", [2000, 2001, 2002])
def test_supported_and_newer_minor_versions(processor, scan, payload, caplog, version):
    payload[:2] = version.to_bytes(2, "big")
    assert processor.process_tag(scan, tag(record(payload))) is not None
    assert ("newer than supported" in caplog.text) == (version > 2001)


@pytest.mark.parametrize("version", [0, 1003, 3000])
def test_unsupported_major_versions(processor, scan, payload, version):
    payload[:2] = version.to_bytes(2, "big")
    assert processor.process_tag(scan, tag(record(payload))) is None


@pytest.mark.parametrize("payload", [b"", b"\x07"])
def test_missing_version(processor, scan, payload):
    assert processor.process_tag(scan, tag(record(payload))) is None


def test_short_payload_and_target_fallback(processor, scan, payload):
    payload[132:139] = bytes(7)
    # The record actually ends after target temperature; missing fields are zero.
    result = processor.process_tag(scan, tag(record(payload[:145])))
    assert result.hotend_min_temp_c == result.hotend_max_temp_c == 215
    assert result.weight_grams == result.bed_temp_c == result.td == 0
    assert result.manufacturing_date == "0001-01-01"
    assert decode_payload(payload[:145], SCHEMAS[2])["mfg_time"] is None


def test_bed_temp_falls_back_to_range(processor, scan, payload):
    # The spec stores a bed target alongside a min/max pair. A tag that fills in
    # only the range should still yield a bed temperature, mirroring the existing
    # print-temperature fallback rather than reporting 0.
    payload[148] = 0
    payload[149:151] = bytes([11, 13])
    assert processor.process_tag(scan, tag(record(payload))).bed_temp_c == 55
    payload[149] = 0
    assert processor.process_tag(scan, tag(record(payload))).bed_temp_c == 65
    payload[150] = 0
    assert processor.process_tag(scan, tag(record(payload))).bed_temp_c == 0


def test_primary_transparent_black_and_cf_modifier(processor, scan, payload):
    payload[60:76] = bytes(16)
    payload[7:12] = b"CF\x00\x00\x00"
    result = processor.process_tag(scan, tag(record(payload)))
    assert result.colors == [0]
    assert result.type == "PLA-CF"
    assert result.modifiers == []


@pytest.mark.parametrize("offset,value", [(12, 255), (134, 13), (136, 25), (145, 60)])
def test_invalid_text_date_time_or_temperature(processor, scan, payload, offset, value):
    payload[offset] = value
    assert processor.process_tag(scan, tag(record(payload))) is None


def test_unknown_material_fails_cleanly(processor, scan, payload):
    payload[2:7] = b"XXXXX"
    assert processor.process_tag(scan, tag(record(payload))) is None


def test_unrelated_mime(processor, scan, payload):
    assert processor.process_tag(scan, tag(record(payload, b"application/other"))) is None


def test_truncated_payload_record(processor, scan, payload):
    assert processor.process_tag(scan, tag(record(payload))[:-8]) is None


def test_all_schema_fields(payload):
    expected_path = Path(__file__).parent / "tags/OpenTag3D/Polar Filament PLA Pure Light Blue.decoded.yml"
    expected = yaml.safe_load(expected_path.read_text())
    actual = decode_payload(payload, SCHEMAS[2])
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        assert actual[key] == (pytest.approx(value) if isinstance(value, float) else value)


def test_schema_controls_new_fields_offsets_and_scaling(payload):
    schema = copy.deepcopy(SCHEMAS[2])
    schema["core"]["fields"].append({"id": "future_field", "type": "int", "start": "0x9E", "length": 2, "scaling": 0.5})
    assert decode_payload(payload, schema)["future_field"] == 500


def test_no_schema_io_during_scans(processor, scan, payload, monkeypatch):
    def unexpected_read(*args, **kwargs):
        pytest.fail("Schema should be loaded only once at module import")
    monkeypatch.setattr(Path, "read_text", unexpected_read)
    assert processor.process_tag(scan, tag(record(payload))) is not None
    assert processor.process_tag(scan, tag(record(payload))) is not None


def test_identity_is_stable_and_tag_specific(processor, scan, payload):
    original = processor.process_tag(scan, tag(record(payload))).unique_id
    payload[76:83] = b"BATCH-8"
    assert processor.process_tag(scan, tag(record(payload))).unique_id == original
    scan.uid = b"\x05\x06\x07\x08"
    assert processor.process_tag(scan, tag(record(payload))).unique_id != original


def test_long_payload_ignores_reserved_extension_bytes(processor, scan, payload):
    payload.extend(bytes(80))
    result = processor.process_tag(scan, tag(record(payload, long=True)))
    assert result.diameter_mm == 1.75
    assert result.weight_grams == 1000


def test_configuration_runtime_and_webhook(scan, payload, monkeypatch):
    # Import the application's real configuration factory without Linux-only
    # GPIO/SPI modules; this test never constructs or accesses physical hardware.
    monkeypatch.setitem(sys.modules, "gpiod", ModuleType("gpiod"))
    monkeypatch.setitem(sys.modules, "spidev", ModuleType("spidev"))
    import config.config_manager as manager
    from main import consume_config
    from exporters.exporter import ExporterEvent

    monkeypatch.setattr(manager, "LOADED_MODULES", [])
    runtime = consume_config({
        "opentag3d_tag_processor enabled": {},
        "opentag3d_tag_processor disabled": {"enabled": "false"},
        "webhook_exporter": {
            "event": "tag_read", "url": "https://example.test/filament",
            "body_json_template": '{"type":"{{ filament.type }}","min_temp":{{ filament.hotend_min_temp_c }}}',
        },
    })
    assert [p.name for p in runtime.mifare_ultralight_processors] == ["enabled"]
    reader = SimpleNamespace(
        start_session=lambda: None, end_session=lambda: None,
        scan=lambda: scan, read_mifare_ultralight=lambda _: tag(record(payload)),
        name="test_reader", slot=0,
    )
    filament, retry = runtime.process_mifare_ultralight(reader, scan)
    assert filament is not None and not retry
    requests = []
    def capture_request(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(raise_for_status=lambda: None)
    monkeypatch.setattr("exporters.webhook.requests.request", capture_request)
    runtime._notify_exporters(scan, filament, reader, ExporterEvent.TAG_READ)
    assert requests[0]["json"] == {"type": "PLA", "min_temp": 205}
