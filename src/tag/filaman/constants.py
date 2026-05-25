class FilamentTypeExtendedData:
    def __init__(self, bed_temp_c: float, drying_temp_c: float, drying_time_hours: float):
        self.bed_temp_c = bed_temp_c
        self.drying_temp_c = drying_temp_c
        self.drying_time_hours = drying_time_hours

FILAMENT_TYPE_TO_EXTENDED_DATA = {
    "PLA": FilamentTypeExtendedData(60.0, 50.0, 8.0),
    "PETG": FilamentTypeExtendedData(70.0, 65.0, 8.0),
    "ABS": FilamentTypeExtendedData(100.0, 80.0, 8.0),
    "TPU": FilamentTypeExtendedData(50.0, 70.0, 8.0),
    "NYLON": FilamentTypeExtendedData(100.0, 80.0, 8.0),
}