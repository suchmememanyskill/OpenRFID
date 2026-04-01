import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TigerTagRegistry:
    version_ids: dict[int, str]
    material_ids: dict[int, str]
    aspect_ids: dict[int, str]
    type_ids: dict[int, str]
    diameter_ids: dict[int, float]
    brand_ids: dict[int, str]
    unit_ids: dict[int, str]


_JSON_FILES = {
    "version_ids": "id_version.json",
    "material_ids": "id_material.json",
    "aspect_ids": "id_aspect.json",
    "type_ids": "id_type.json",
    "diameter_ids": "id_diameter.json",
    "brand_ids": "id_brand.json",
    "unit_ids": "id_measure_unit.json",
}
_JSON_DIRECTORY = "database"

_REGISTRY_CACHE: TigerTagRegistry | None = None


def get_tigertag_registry() -> TigerTagRegistry:
    global _REGISTRY_CACHE

    if _REGISTRY_CACHE is None:
        _REGISTRY_CACHE = _load_registry()

    return _REGISTRY_CACHE


def _load_registry() -> TigerTagRegistry:
    base_path = Path(__file__).resolve().parent / _JSON_DIRECTORY

    version_ids = _load_id_map(
        base_path / _JSON_FILES["version_ids"],
        ("name", "label", "title", "description", "version"),
        str,
        {},
    )

    return TigerTagRegistry(
        version_ids=version_ids,
        material_ids=_load_id_map(
            base_path / _JSON_FILES["material_ids"],
            ("name", "label", "title", "description"),
            str,
            {},
        ),
        aspect_ids=_load_id_map(
            base_path / _JSON_FILES["aspect_ids"],
            ("name", "label", "title", "description"),
            str,
            {},
        ),
        type_ids=_load_id_map(
            base_path / _JSON_FILES["type_ids"],
            ("name", "label", "title", "description"),
            str,
            {},
        ),
        diameter_ids=_load_id_map(
            base_path / _JSON_FILES["diameter_ids"],
            ("diameter", "value", "name", "label", "title"),
            _to_float,
            {},
        ),
        brand_ids=_load_id_map(
            base_path / _JSON_FILES["brand_ids"],
            ("name", "label", "title", "description", "brand"),
            str,
            {},
        ),
        unit_ids=_load_id_map(
            base_path / _JSON_FILES["unit_ids"],
            ("name", "label", "title", "description", "symbol", "unit"),
            str,
            {},
        ),
    )


def _load_id_map(
    path: Path,
    label_fields: tuple[str, ...],
    transform,
    fallback: dict[int, Any],
) -> dict[int, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(fallback)

    entries = _extract_entries(payload)
    mapped: dict[int, Any] = {}

    if isinstance(entries, dict):
        for key, value in entries.items():
            entry_id = _coerce_int(key)
            if entry_id is None:
                continue

            if isinstance(value, dict):
                label = _extract_label(value, label_fields)
                if label is None:
                    continue
                mapped[entry_id] = transform(label)
            else:
                mapped[entry_id] = transform(value)
    else:
        for item in entries:
            if not isinstance(item, dict):
                continue

            entry_id = _extract_id(item)
            if entry_id is None:
                continue

            label = _extract_label(item, label_fields)
            if label is None:
                continue

            mapped[entry_id] = transform(label)

    return mapped or dict(fallback)


def _extract_entries(payload: Any) -> Any:
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    for key in ("data", "items", "results", "response", "content"):
        value = payload.get(key)
        if isinstance(value, (list, dict)):
            return value

    return payload


def _extract_id(item: dict[str, Any]) -> int | None:
    for key in ("id", "value", "code", "identifier"):
        if key in item:
            return _coerce_int(item[key])

    return None


def _extract_label(item: dict[str, Any], label_fields: tuple[str, ...]) -> Any | None:
    for field in label_fields:
        value = item.get(field)
        if value not in (None, ""):
            return value

    return None


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None

        try:
            return int(stripped, 0)
        except ValueError:
            return None

    return None


def _to_float(value: Any) -> float:
    return float(value)
