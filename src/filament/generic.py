import hashlib
import logging
from .valid_materials import VALID_BASE_MATERIALS

# ---------------------------------------------------------------------------
# Filament type normaliser
# ---------------------------------------------------------------------------
# Resolves non-standard filament type strings (e.g. "PLA+", "ABS+",
# "PETG-RAPID") to a valid VALID_BASE_MATERIALS entry before GenericFilament
# raises ValueError.
#
# Many real-world tags — including Spoolman's predefined filament database —
# use type strings that are not in VALID_BASE_MATERIALS. Without normalisation
# any such tag causes OpenRFID to fire tag_parse_error instead of tag_read,
# so exporters never receive filament data.
#
# Resolution order:
#   Step 1  Exact match against VALID_BASE_MATERIALS          (always active)
#   Step 2  Explicit type_map from configuration              (always active when set)
#   Step 3  Strip trailing '+': ABS+ → ABS                   (type_normalizer_strip_plus = true)
#   Step 4  Longest-prefix match: PETG-RAPID → PETG          (type_normalizer_prefix_match = true)
#
# Call init_type_normalizer() once at startup (after loading Configuration).
# ---------------------------------------------------------------------------

_USER_MAP:      dict[str, str] = {}
_STRIP_PLUS:    bool = False
_PREFIX_MATCH:  bool = False


def init_type_normalizer(
    type_map:      dict[str, str],
    strip_plus:    bool,
    prefix_match:  bool,
) -> None:
    """Initialise module-level normaliser state from a loaded Configuration."""
    global _USER_MAP, _STRIP_PLUS, _PREFIX_MATCH
    _USER_MAP     = type_map
    _STRIP_PLUS   = strip_plus
    _PREFIX_MATCH = prefix_match
    logging.info(
        f"OpenRFID type normaliser: {len(_USER_MAP)} map entries, "
        f"strip_plus={_STRIP_PLUS}, prefix_match={_PREFIX_MATCH}"
    )


def _derive_material_type(raw: str) -> tuple[str | None, str | None]:
    """
    Attempt to derive a valid VALID_BASE_MATERIALS entry from a non-standard type string.

    Returns (derived_type, step_name) or (None, None) if unresolvable.
    """
    # Step 1: already valid — no normalisation needed
    if raw in VALID_BASE_MATERIALS:
        return raw, None

    # Step 2: explicit user map
    if raw in _USER_MAP:
        return _USER_MAP[raw], "type_map"

    stripped = raw.rstrip('+')

    # Step 3: strip trailing '+'
    if _STRIP_PLUS and stripped in VALID_BASE_MATERIALS:
        return stripped, "strip_plus"

    # Step 4: longest-prefix match
    if _PREFIX_MATCH:
        for valid in sorted(VALID_BASE_MATERIALS, key=len, reverse=True):
            if raw.startswith(valid) or stripped.startswith(valid):
                return valid, "prefix_match"

    return None, None


def to_rgba(argb: int) -> int:
    a = (argb >> 24) & 0xFF
    r = (argb >> 16) & 0xFF
    g = (argb >> 8) & 0xFF
    b = argb & 0xFF

    rgba = (r << 24) | (g << 16) | (b << 8) | a
    return rgba

class GenericFilament:
    def __init__(self,
                 source_processor: str,
                 unique_id: str,
                 manufacturer: str,
                 type: str, # TODO: Should probably be an enum?
                 modifiers: list[str],
                 colors : list[int], # Format 0xAARRGGBB
                 diameter_mm: float,
                 weight_grams: float,
                 hotend_min_temp_c: float,
                 hotend_max_temp_c: float,
                 bed_temp_c: float,
                 drying_temp_c: float,
                 drying_time_hours: float,
                 manufacturing_date: str, # ISO 8601 date string
                 td: float = 0.0 # Transmission Distance in mm for HueForge/OrcaSlicer-FullSpectrum
                 ):
        self.source_processor = source_processor
        self.unique_id = unique_id
        self.manufacturer = manufacturer
        self.type = type
        self.modifiers = modifiers
        self.colors = colors
        self.diameter_mm = diameter_mm
        self.weight_grams = weight_grams
        self.hotend_min_temp_c = hotend_min_temp_c
        self.hotend_max_temp_c = hotend_max_temp_c
        self.bed_temp_c = bed_temp_c
        self.drying_temp_c = drying_temp_c
        self.drying_time_hours = drying_time_hours
        self.manufacturing_date = manufacturing_date
        self.td = td

        if "CF" in self.modifiers:
            self.type += "-CF"
            self.modifiers.remove("CF")
        
        if "GF" in self.modifiers:
            self.type += "-GF"
            self.modifiers.remove("GF")

        if self.type not in VALID_BASE_MATERIALS:
            derived, via = _derive_material_type(self.type)
            if derived:
                logging.warning(
                    f"OpenRFID: non-standard filament type '{self.type}' "
                    f"normalised to '{derived}' (via {via})"
                )
                self.type = derived
            else:
                raise ValueError(f"Invalid filament type: {self.type}")

    def pretty_text(self) -> str:
        modifiers = ' '.join(self.modifiers)

        if modifiers:
            modifiers += " "

        return "\n".join([
            f"{self.manufacturer} {self.type} {modifiers}Filament (processed by {self.source_processor}):",
            f"- Color (ARGB): {' '.join([f'#{color:06X}' for color in self.colors])}",
            f"- Diameter: {self.diameter_mm:.2f} mm",
            f"- Weight: {self.weight_grams} grams",
            f"- Hotend Temp: {self.hotend_min_temp_c:.1f}C - {self.hotend_max_temp_c:.1f}C",
            f"- Bed Temp: {self.bed_temp_c:.1f}C",
            f"- Drying: {self.drying_temp_c:.1f}C for {self.drying_time_hours:.1f} hours",
            f"- Manufactured on: {self.manufacturing_date}",
            f"- TD: {self.td:.1f} mm"
        ])

    @property
    def rgba(self) -> int:
        if not self.colors or len(self.colors) == 0:
            return 0x00000000  # Transparent if no color available
        
        argb = self.colors[0]
        return to_rgba(argb)
    
    def to_dict(self) -> dict:
        return {
            "source_processor": self.source_processor,
            "unique_id": self.unique_id,
            "manufacturer": self.manufacturer,
            "type": self.type,
            "modifiers": self.modifiers,
            "colors": self.colors,
            "rgba": self.rgba,
            "rgb": (self.rgba >> 8) & 0xFFFFFF,
            "alpha": self.rgba & 0xFF,
            "colors_rgba": [to_rgba(color) for color in self.colors],
            "colors_rgba_hex": [f"{to_rgba(color):08X}" for color in self.colors],
            "diameter_mm": self.diameter_mm,
            "weight_grams": self.weight_grams,
            "hotend_min_temp_c": self.hotend_min_temp_c,
            "hotend_max_temp_c": self.hotend_max_temp_c,
            "bed_temp_c": self.bed_temp_c,
            "drying_temp_c": self.drying_temp_c,
            "drying_time_hours": self.drying_time_hours,
            "manufacturing_date": self.manufacturing_date,
            "td": self.td
        }
    
    @staticmethod
    def generate_unique_id(*args) -> str:
        strings = "|".join([str(arg) for arg in args])
        hash = hashlib.sha256(strings.encode('utf-8')).hexdigest()
        return hash