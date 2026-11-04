import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from filament.valid_materials import VALID_BASE_MATERIALS
from tag.snapmaker import constants as Constants


@pytest.mark.parametrize(
    "code,name",
    [
        (code, name)
        for code, name in Constants.FILAMENT_PROTO_MAIN_TYPE_MAPPING.items()
        if code != Constants.FILAMENT_PROTO_MAIN_TYPE_RESERVED
    ],
)
def test_snapmaker_main_type_is_valid_material(code: int, name: str) -> None:
    assert name in VALID_BASE_MATERIALS, f"Snapmaker main type {code} ({name}) is not a valid base material"
