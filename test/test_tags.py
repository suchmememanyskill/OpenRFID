import os
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from reader.scan_result import ScanResult
from tag.anycubic.processor import AnycubicTagProcessor
from tag.bambu.processor import BambuTagProcessor
from tag.creality.processor import CrealityTagProcessor
from tag.elegoo.processor import ElegooTagProcessor
from tag.openspool.processor import OpenspoolTagProcessor
from tag.qidi.processor import QidiTagProcessor
from tag.snapmaker.processor import SnapmakerTagProcessor
from tag.spoolease.processor import SpooleaseTagProcessor
from tag.tag_processor import TagProcessor
from tag.tag_types import TagType
from tag.tigertag.processor import TigerTagProcessor


FIXTURES_ROOT = Path(__file__).resolve().parent / "tags"

BAMBU_KEY_ENV_VAR = "FILAMENT_DETECT_TEST_BAMBU_KEY"
CREALITY_KEY_ENV_VAR = "FILAMENT_DETECT_TEST_CREALITY_KEY"
CREALITY_ENCRYPTION_KEY_ENV_VAR = "FILAMENT_DETECT_TEST_CREALITY_ENCRYPTION_KEY"


def _collect_fixture_cases() -> list[Path]:
    return sorted(FIXTURES_ROOT.glob("*/*.bin"))


def _read_required_environment_variable(name: str, processor_name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Skipping {processor_name} fixtures: missing environment variable {name}")
    return value


def _build_anycubic_processor() -> TagProcessor:
    processor = AnycubicTagProcessor(
        {
            "__name": "AnycubicTagProcessor",
        }
    )
    processor.enabled = True
    return processor


def _build_bambu_processor() -> TagProcessor:
    processor = BambuTagProcessor(
        {
            "__name": "BambuTagProcessor",
            "key": "0",
        }
    )
    processor.enabled = True
    return processor


def _build_creality_processor() -> TagProcessor:
    processor = CrealityTagProcessor(
        {
            "__name": "CrealityTagProcessor",
            "key": "0",
            "encryption_key": _read_required_environment_variable(CREALITY_ENCRYPTION_KEY_ENV_VAR, "Creality"),
        }
    )
    processor.enabled = True
    assert processor.encryption_key is not None, (
        "Creality processor fixture is missing a valid encryption key. "
        f"Check {CREALITY_ENCRYPTION_KEY_ENV_VAR}."
    )
    return processor


def _build_elegoo_processor() -> TagProcessor:
    processor = ElegooTagProcessor(
        {
            "__name": "ElegooTagProcessor",
        }
    )
    processor.enabled = True
    return processor


def _build_openspool_processor() -> TagProcessor:
    processor = OpenspoolTagProcessor(
        {
            "__name": "OpenspoolTagProcessor",
        }
    )
    processor.enabled = True
    return processor


def _build_qidi_processor() -> TagProcessor:
    processor = QidiTagProcessor(
        {
            "__name": "QidiTagProcessor",
        }
    )
    processor.enabled = True
    return processor


def _build_spoolease_processor() -> TagProcessor:
    processor = SpooleaseTagProcessor(
        {
            "__name": "SpooleaseTagProcessor",
        }
    )
    processor.enabled = True
    return processor


def _build_snapmaker_processor() -> TagProcessor:
    processor = SnapmakerTagProcessor(
        {
            "__name": "SnapmakerTagProcessor",
            "key": "536e61706d616b65725f71776572747975696f705b2c2e3b5d5f317132773365",
        }
    )
    processor.enabled = True
    return processor


def _build_tigertag_processor() -> TagProcessor:
    processor = TigerTagProcessor(
        {
            "__name": "TigerTagProcessor",
        }
    )
    processor.enabled = True
    return processor


PROCESSOR_FIXTURES = {
    "Anycubic": {
        "build_processor": _build_anycubic_processor,
        "tag_type": TagType.MifareUltralight,
    },
    "Bambu": {
        "build_processor": _build_bambu_processor,
        "tag_type": TagType.MifareClassic1k,
    },
    "Creality": {
        "build_processor": _build_creality_processor,
        "tag_type": TagType.MifareClassic1k,
    },
    "Elegoo": {
        "build_processor": _build_elegoo_processor,
        "tag_type": TagType.MifareUltralight,
    },
    "OpenSpool": {
        "build_processor": _build_openspool_processor,
        "tag_type": TagType.MifareUltralight,
    },
    "Qidi": {
        "build_processor": _build_qidi_processor,
        "tag_type": TagType.MifareClassic1k,
    },
    "SpoolEase": {
        "build_processor": _build_spoolease_processor,
        "tag_type": TagType.MifareUltralight,
    },
    "Snapmaker": {
        "build_processor": _build_snapmaker_processor,
        "tag_type": TagType.MifareClassic1k,
    },
    "Tigertag": {
        "build_processor": _build_tigertag_processor,
        "tag_type": TagType.MifareUltralight,
    },
}


def _get_processor_fixture(folder_name: str) -> dict:
    if folder_name not in PROCESSOR_FIXTURES:
        raise AssertionError(
            f"No processor fixture definition found for folder '{folder_name}'. "
            "Add it to PROCESSOR_FIXTURES in test/tags.py."
        )

    return PROCESSOR_FIXTURES[folder_name]


def _build_scan_result(tag_type: TagType) -> ScanResult:
    return ScanResult(
        tag_type=tag_type,
        uid=b"\x01\x02\x03\x04",
        atqa=b"\x00\x44",
        bcc=b"\x00",
        sak=b"\x00",
    )


def _assert_expected_matches_actual(expected, actual, path: str = "root") -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"

        for key, expected_value in expected.items():
            _assert_expected_matches_actual(expected_value, actual[key], f"{path}.{key}")
        return

    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        assert len(actual) == len(expected), f"{path}: expected {len(expected)} items, got {len(actual)}"

        for index, expected_value in enumerate(expected):
            _assert_expected_matches_actual(expected_value, actual[index], f"{path}[{index}]")
        return

    if isinstance(expected, float):
        assert actual == pytest.approx(expected), f"{path}: expected {expected!r}, got {actual!r}"
        return

    assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"

@pytest.mark.parametrize("fixture_path", _collect_fixture_cases(), ids=lambda path: path.stem)
def test_tag_processor_fixture_matches_expected_output(fixture_path: Path) -> None:
    folder_name = fixture_path.parent.name
    expected_path = fixture_path.with_suffix(".yml")
    processor_fixture = _get_processor_fixture(folder_name)    

    processor = processor_fixture["build_processor"]()
    filament = processor.process_tag(
        _build_scan_result(processor_fixture["tag_type"]),
        fixture_path.read_bytes(),
    )

    #if not expected_path.exists():
    #    yaml.safe_dump(filament.to_dict(), expected_path.open("w", encoding="utf-8"))

    assert expected_path.exists(), f"Missing expected output file for {fixture_path.name}"
    assert filament is not None, f"{folder_name} returned no filament for {fixture_path.name}"

    expected = yaml.safe_load(expected_path.read_text(encoding="utf-8"))
    actual = filament.to_dict()

    _assert_expected_matches_actual(expected, actual)
