import os
from pathlib import Path

import requests


JSON_FILES = [
    ("https://api.tigertag.io/api:tigertag/version/get/all", "id_version.json"),
    ("https://api.tigertag.io/api:tigertag/material/get/all", "id_material.json"),
    ("https://api.tigertag.io/api:tigertag/aspect/get/all", "id_aspect.json"),
    ("https://api.tigertag.io/api:tigertag/type/get/all", "id_type.json"),
    ("https://api.tigertag.io/api:tigertag/diameter/filament/get/all", "id_diameter.json"),
    ("https://api.tigertag.io/api:tigertag/brand/get/all", "id_brand.json"),
    ("https://api.tigertag.io/api:tigertag/measure_unit/get/all", "id_measure_unit.json"),
]
JSON_DIRECTORY = "database"


def download_json_files(target_folder: str | None = None, timeout: float = 10.0):
    base_directory = Path(target_folder or os.path.dirname(os.path.abspath(__file__)))
    destination = base_directory / JSON_DIRECTORY
    destination.mkdir(parents=True, exist_ok=True)

    for url, filename in JSON_FILES:
        file_path = destination / filename
        try:
            print(f"Downloading {url}...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            file_path.write_text(response.text, encoding="utf-8")
            print(f"Saved: {file_path}")
        except Exception as exc:
            print(f"Failed to download {url}: {exc}")


if __name__ == "__main__":
    download_json_files()
