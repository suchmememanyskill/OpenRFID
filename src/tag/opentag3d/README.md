# OpenTag3D

Enable offline reading with `[opentag3d_tag_processor]` in the configuration.
The processor supports the 2.x layout through specification 2.004. Newer 2.x
versions are attempted with a warning; other major versions are rejected.
No network access or extra dependencies are needed at runtime.

`schemas/v2.json` is an unmodified copy of the official
[spec.json](https://opentag3d.info/spec.json), version 2.004, downloaded on
2026-10-27. See the [specification](https://opentag3d.info/spec.html) and its
GPL-3.0 license. The schemas are loaded once on module import. Offsets, lengths,
types, and scaling come from JSON; the mapping to `GenericFilament` is explicit.

## Updating support

1. Review the upstream schema changes and replace `schemas/v2.json` for compatible
   2.x updates. For an incompatible major release, add a separate schema file and
   register it in `schema.py`; retain existing layouts for older tags.
2. Add decoding for any new field types. Newly declared fields of existing types
   are automatically decoded internally. Exporting them requires an explicit
   mapping to an existing `GenericFilament` field.
3. Update the adapter only when new fields need common `GenericFilament` mappings
   or their meaning changes. A schema update cannot implement semantic changes.
4. Add independent binary fixtures and expected YAML results, then run `pytest`.
   Do not regenerate expected values from the decoder or generate fixture offsets
   from the schema being tested. Verify physical NTAG215 reads before release.

## Mapping choices

- Only fields supported by the existing `GenericFilament` model are exported.
  Additional fields such as SKU, barcode, and chamber temperature are decoded
  internally but not exported. The online data URL is not fetched.
  The shared filament model and NDEF parser are unchanged.
- Missing payload bytes are zero-filled. Missing dates use the library's
  `0001-01-01` default; invalid nonzero dates and malformed UTF-8 reject the record.
- Missing print temperature bounds fall back to the target temperature.
- Primary color is retained even when transparent; transparent-black secondary
  colors are omitted. Exported colors use ARGB.
- Weight is the nominal filament weight, not measured weight or remaining weight.
- The unique ID hashes the physical tag UID, since a serial may identify a batch.
- Material names still follow `GenericFilament`'s existing supported-material
  validation; unrecognized materials fail cleanly rather than becoming PLA.
- This adds reading, not tag writing or legacy v1 support. The physical reader's
  existing NTAG215-sized read limit is unchanged.

The existing shared NDEF parser limitations also apply to this processor,
including NULL TLV padding and incomplete validation of malformed or chunked
messages. Parser hardening should be a separate change with shared-format tests.
