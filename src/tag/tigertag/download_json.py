"""Sync the TigerTag reference tables in ``database/``.

Follows the sync strategy from the TigerTag RFID Guide (section 2.0):
fetch the ``last_update`` manifest first, then download only the tables
whose timestamp changed. The live TigerTag API is the primary source; if
it is unreachable, the whole run falls back to the GitHub mirror of the
guide, so the manifest and the tables always come from the same source.

Tables are written indented, one entry per line, so updates produce
readable diffs. A table is only replaced once its download has been
validated, so a failed run never leaves a truncated file behind.

Usage:
    python download_json.py [--force] [--summary FILE]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests


API_BASE = "https://api.tigertag.io/api:tigertag"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/TigerTag-Project/TigerTag-RFID-Guide/main/database"

# last_update key -> (API endpoint, file name locally and on the GitHub mirror)
DATASETS = {
    "versions": ("version/get/all", "id_version.json"),
    "types": ("type/get/all", "id_type.json"),
    "brands": ("brand/get/all", "id_brand.json"),
    "filament_diameters": ("diameter/filament/get/all", "id_diameter.json"),
    "filament_materials": ("material/get/all", "id_material.json"),
    "aspects": ("aspect/get/all", "id_aspect.json"),
    "measure_units": ("measure_unit/get/all", "id_measure_unit.json"),
}
LAST_UPDATE_FILE = "last_update.json"
JSON_DIRECTORY = "database"

_LABEL_FIELDS = ("name", "label", "title", "description", "symbol", "tag")


def _fetch_json(url: str, timeout: float):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _pick_source(timeout: float):
    """Return (source name, remote manifest, url builder) for this run."""
    try:
        manifest = _fetch_json(f"{API_BASE}/all/last_update", timeout)
        return "api", manifest, lambda endpoint, filename: f"{API_BASE}/{endpoint}"
    except (requests.RequestException, ValueError) as exc:
        print(f"TigerTag API unreachable ({exc}), falling back to the GitHub mirror", file=sys.stderr)
        manifest = _fetch_json(f"{GITHUB_RAW_BASE}/{LAST_UPDATE_FILE}", timeout)
        return "github", manifest, lambda endpoint, filename: f"{GITHUB_RAW_BASE}/{filename}"


def _read_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp_path, path)


def _entries_by_id(data) -> dict:
    if not isinstance(data, list):
        return {}
    return {entry["id"]: entry for entry in data if isinstance(entry, dict) and "id" in entry}


def _label(entry: dict) -> str:
    for field in _LABEL_FIELDS:
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _describe_changes(filename: str, old_data, new_data) -> list[str]:
    old, new = _entries_by_id(old_data), _entries_by_id(new_data)
    added = [new[key] for key in new if key not in old]
    removed = [old[key] for key in old if key not in new]
    changed = [new[key] for key in new if key in old and new[key] != old[key]]

    lines = [f"### `{filename}`: {len(old)} → {len(new)} entries"]
    for title, entries in (("Added", added), ("Removed", removed), ("Changed", changed)):
        if entries:
            items = ", ".join(f"{_label(entry) or '?'} ({entry['id']})" for entry in entries)
            lines.append(f"- **{title}** ({len(entries)}): {items}")
    if not (added or removed or changed):
        lines.append("- Formatting only, no entry changed")
    return lines


def download_json_files(target_folder: str | None = None, timeout: float = 30.0,
                        force: bool = False) -> tuple[list[str], list[str]]:
    """Sync the tables. Returns (updated file names, markdown change summary)."""
    base_directory = Path(target_folder or os.path.dirname(os.path.abspath(__file__)))
    destination = base_directory / JSON_DIRECTORY
    destination.mkdir(parents=True, exist_ok=True)

    source, remote_manifest, url_for = _pick_source(timeout)
    print(f"Source: {source}")

    last_update_path = destination / LAST_UPDATE_FILE
    local_manifest = _read_json(last_update_path) or {}
    synced_manifest = dict(local_manifest)
    updated: list[str] = []
    summary: list[str] = []
    failures: list[str] = []

    for key, (endpoint, filename) in DATASETS.items():
        file_path = destination / filename
        remote_ts = remote_manifest.get(key)
        if not force and remote_ts is not None and remote_ts == local_manifest.get(key) and file_path.exists():
            print(f"Up to date: {filename}")
            continue

        url = url_for(endpoint, filename)
        try:
            print(f"Downloading {url}...")
            data = _fetch_json(url, timeout)
            if not isinstance(data, list) or not data:
                raise ValueError("expected a non-empty JSON array")
        except (requests.RequestException, ValueError) as exc:
            print(f"Failed to download {url}: {exc}", file=sys.stderr)
            failures.append(filename)
            continue

        old_text = file_path.read_text(encoding="utf-8") if file_path.exists() else None
        old_data = _read_json(file_path)
        _write_json(file_path, data)
        if remote_ts is not None:
            synced_manifest[key] = remote_ts
        if file_path.read_text(encoding="utf-8") != old_text:
            updated.append(filename)
            summary += _describe_changes(filename, old_data, data) + [""]
            print(f"Updated: {file_path}")
        else:
            print(f"Unchanged: {filename}")

    if synced_manifest != local_manifest:
        _write_json(last_update_path, synced_manifest)

    if failures:
        raise RuntimeError(f"Failed to download: {', '.join(failures)}")
    return updated, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="download every table, even if its timestamp did not change")
    parser.add_argument("--summary", type=Path,
                        help="write a markdown summary of the changes to this file")
    args = parser.parse_args()

    try:
        updated, summary = download_json_files(force=args.force)
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.summary:
        args.summary.write_text("\n".join(summary), encoding="utf-8")
    print(f"Updated {len(updated)} table(s)" if updated else "All tables already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
