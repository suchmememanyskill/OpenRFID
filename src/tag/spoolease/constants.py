class FilamentTypeExtendedData:
    def __init__(
        self, bed_temp_c: float, drying_temp_c: float, drying_time_hours: float
    ):
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
    "ABS": FilamentTypeExtendedData(95.0, 80.0, 8.0),
    "ABS-GF": FilamentTypeExtendedData(95.0, 80.0, 8.0),
    "ABS-S": FilamentTypeExtendedData(95.0, 80.0, 8.0),
    "ASA": FilamentTypeExtendedData(95.0, 80.0, 8.0),
    "ASA-AERO": FilamentTypeExtendedData(85.0, 80.0, 8.0),
    "ASA-CF": FilamentTypeExtendedData(95.0, 80.0, 8.0),
    "BVOH": FilamentTypeExtendedData(60.0, 60.0, 6.0),
    "EVA": FilamentTypeExtendedData(55.0, 50.0, 6.0),
    "HIPS": FilamentTypeExtendedData(100.0, 70.0, 6.0),
    "PA": FilamentTypeExtendedData(110.0, 80.0, 10.0),
    "PA-CF": FilamentTypeExtendedData(110.0, 80.0, 10.0),
    "PA-GF": FilamentTypeExtendedData(110.0, 80.0, 10.0),
    "PA-S": FilamentTypeExtendedData(110.0, 80.0, 10.0),
    "PA6-CF": FilamentTypeExtendedData(110.0, 80.0, 10.0),
    "PC": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "PCTG": FilamentTypeExtendedData(80.0, 65.0, 6.0),
    "PE": FilamentTypeExtendedData(60.0, 60.0, 6.0),
    "PE-CF": FilamentTypeExtendedData(60.0, 60.0, 6.0),
    "PET-CF": FilamentTypeExtendedData(85.0, 80.0, 10.0),
    "PETG": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "PETG-CF": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "PHA": FilamentTypeExtendedData(60.0, 50.0, 6.0),
    "PLA": FilamentTypeExtendedData(55.0, 50.0, 8.0),
    "PLA-AERO": FilamentTypeExtendedData(45.0, 50.0, 8.0),
    "PLA-CF": FilamentTypeExtendedData(60.0, 55.0, 8.0),
    "PLA-S": FilamentTypeExtendedData(45.0, 50.0, 8.0),
    "PP": FilamentTypeExtendedData(90.0, 70.0, 12.0),
    "PP-CF": FilamentTypeExtendedData(90.0, 70.0, 12.0),
    "PP-GF": FilamentTypeExtendedData(90.0, 70.0, 12.0),
    "PPA-CF": FilamentTypeExtendedData(110.0, 120.0, 10.0),
    "PPA-GF": FilamentTypeExtendedData(110.0, 120.0, 10.0),
    "PPS": FilamentTypeExtendedData(110.0, 120.0, 10.0),
    "PPS-CF": FilamentTypeExtendedData(110.0, 120.0, 10.0),
    "PVA": FilamentTypeExtendedData(45.0, 60.0, 8.0),
    "TPU": FilamentTypeExtendedData(38.0, 70.0, 8.0),
    "TPU-AMS": FilamentTypeExtendedData(33.0, 70.0, 8.0),
}
