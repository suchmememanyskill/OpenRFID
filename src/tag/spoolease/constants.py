class FilamentTypeExtendedData:
    def __init__(self, bed_temp_c: float, drying_temp_c: float, drying_time_hours: float):
        self.bed_temp_c = bed_temp_c
        self.drying_temp_c = drying_temp_c
        self.drying_time_hours = drying_time_hours


FILAMENT_TYPE_ALIASES = {
    "ABS-S": "ABS",
    "PA-S": "PA",
    "PLA-S": "PLA",
    "TPU-AMS": "TPU",
}


FILAMENT_TYPE_TO_EXTENDED_DATA = {
    "ABS": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "ABS-GF": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "ABS-S": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "ASA": FilamentTypeExtendedData(90.0, 80.0, 8.0),
    "ASA-AERO": FilamentTypeExtendedData(90.0, 80.0, 8.0),
    "ASA-CF": FilamentTypeExtendedData(90.0, 80.0, 8.0),
    "BVOH": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "EVA": FilamentTypeExtendedData(50.0, 50.0, 8.0),
    "HIPS": FilamentTypeExtendedData(100.0, 70.0, 8.0),
    "PA": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "PA-CF": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "PA-GF": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "PA-S": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "PA6-CF": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "PC": FilamentTypeExtendedData(110.0, 80.0, 8.0),
    "PCTG": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "PE": FilamentTypeExtendedData(60.0, 60.0, 8.0),
    "PE-CF": FilamentTypeExtendedData(60.0, 60.0, 8.0),
    "PET-CF": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "PETG": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "PETG-CF": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "PHA": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "PLA": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "PLA-AERO": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "PLA-CF": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "PLA-S": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "PP": FilamentTypeExtendedData(80.0, 80.0, 8.0),
    "PP-CF": FilamentTypeExtendedData(80.0, 80.0, 8.0),
    "PP-GF": FilamentTypeExtendedData(80.0, 80.0, 8.0),
    "PPA-CF": FilamentTypeExtendedData(100.0, 100.0, 8.0),
    "PPA-GF": FilamentTypeExtendedData(100.0, 100.0, 8.0),
    "PPS": FilamentTypeExtendedData(110.0, 100.0, 8.0),
    "PPS-CF": FilamentTypeExtendedData(110.0, 100.0, 8.0),
    "PVA": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "TPU": FilamentTypeExtendedData(50.0, 70.0, 8.0),
    "TPU-AMS": FilamentTypeExtendedData(50.0, 70.0, 8.0),
}
