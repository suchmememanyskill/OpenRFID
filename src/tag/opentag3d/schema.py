"""Offline decoding of the official OpenTag3D memory map."""

from datetime import date, time
import json
from pathlib import Path


# Parse the official JSON format so future offsets, lengths, scaling, and fields
# can be updated from the specification instead of being manually implemented
# in Python. Load the bundled schemas once, not on every scan or over the network.
# Source: https://opentag3d.info/spec.json (2.004, downloaded 2026-10-27).
SCHEMAS = {
    2: json.loads((Path(__file__).parent / "schemas" / "v2.json").read_text(encoding="utf-8")),
}
MIME_TYPE = SCHEMAS[2]["mime_type"]


def version_number(version: str) -> int:
    """Convert the schema's version string to the tag's integer version for exact comparisons."""
    # The spec uses three implied decimal places (2.001 -> 2001). Comparing
    # integers avoids floating-point rounding when deciding whether to warn.
    major, minor = version.split(".")
    return int(major) * 1000 + int(minor)


def decode_payload(payload: bytes, schema: dict) -> dict:
    """Apply the official memory map independently of the library's filament model."""
    # Data Structure Standard: offsets are relative to the NDEF payload, not
    # physical tag memory. The caller must remove the NDEF framing first and
    # select the correct major-version schema before calling this helper.
    values = {}
    for field in schema["core"]["fields"]:
        start = int(field["start"], 16)
        length = field["length"]
        # Spec 2.001 says missing payload bytes are zero. Pad each field so a
        # short payload also works when it ends partway through an integer.
        # This does not repair a truncated NDEF message; framing is handled by
        # the shared parser. Undeclared/reserved payload bytes are ignored.
        raw = payload[start:start + length].ljust(length, b"\x00")
        field_type = field["type"]
        if field_type == "int":
            # Integers are unsigned and big-endian. JSON scaling converts to
            # physical units, e.g. 42 -> 210 C, 1750 -> 1.75 mm, 118 -> 11.8 mm TD.
            value = int.from_bytes(raw, "big") * field.get("scaling", 1)
        elif field_type in ("utf8", "ascii"):
            # Strings are UTF-8 unless the field explicitly specifies ASCII
            # (such as the URL). Ignore NUL padding; reject invalid encoding
            # instead of silently altering a material or manufacturer name.
            value = raw.split(b"\x00", 1)[0].decode("utf-8" if field_type == "utf8" else "ascii")
        elif field_type == "rgba":
            # Preserve the spec's four separate R/G/B/A bytes here. Conversion
            # to the library's packed ARGB integer belongs in the adapter.
            value = list(raw)
        elif field_type == "date":
            # Manufacture Date stores a two-byte year, month, and day. Use None
            # for all-zero/missing dates; reject impossible nonzero dates via date().
            value = date(int.from_bytes(raw[:2], "big"), raw[2], raw[3]).isoformat() if any(raw) else None
        elif field_type == "time":
            # Manufacture Time is three UTC hour/minute/second bytes. No local
            # timezone conversion is needed. Our all-zero policy treats missing
            # time and exactly midnight alike; the bytes cannot distinguish them.
            value = time(*raw).isoformat() if any(raw) else None
        else:
            # A new field type needs code review; guessing its representation
            # could silently misread tags after an otherwise simple JSON update.
            raise ValueError(f"Unsupported OpenTag3D schema field type: {field_type}")
        values[field["id"]] = value
    return values
