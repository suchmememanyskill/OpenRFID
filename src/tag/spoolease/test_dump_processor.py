"""Standalone SpoolEase dump test.

Usage:
    
    from OpenRFID root folder:
    python3 src/tag/spoolease/test_dump_processor.py

How it works:
    - Reads the NFC Tools-style page dump from `test_tag_dump.txt`
    - Converts the dumped hex bytes into the raw tag byte buffer expected by OpenRFID
    - Passes the raw bytes to `SpooleaseTagProcessor.process_tag(...)`
    - Prints the parsed filament structure as JSON

To test another tag:
    - Replace the contents of `test_tag_dump.txt` with another NFC Tools dump
    - Re-run the command above
"""

import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reader.scan_result import ScanResult
from tag.spoolease import SpooleaseTagProcessor
from tag.tag_types import TagType


PAGE_PATTERN = re.compile(r"\[\s*([0-9A-Fa-f:]+)\s*\]")


def parse_nfc_tools_dump(dump_text: str) -> bytes:
    raw_bytes = bytearray()

    for line in dump_text.splitlines():
        match = PAGE_PATTERN.search(line)
        if not match:
            continue

        for byte_text in match.group(1).split(":"):
            raw_bytes.append(int(byte_text, 16))

    return bytes(raw_bytes)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    fixture_path = Path(__file__).with_name("test_tag_dump.txt")
    raw_tag_data = parse_nfc_tools_dump(fixture_path.read_text())

    processor = SpooleaseTagProcessor({"__name": "spoolease_test"})
    scan_result = ScanResult(TagType.MifareUltralight, b"\x04\x7B\x1F\x31\xC9\x2A\x81", b"", b"", b"\x00")

    filament = processor.process_tag(scan_result, raw_tag_data)

    if filament is None:
        print("No filament data was parsed.")
        return

    print(json.dumps(filament.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
