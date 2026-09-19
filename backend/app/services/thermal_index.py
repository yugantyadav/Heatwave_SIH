# Thermal index service
from pythermalcomfort import utilities
from app.core.config import settings

class ThermalIndexService:
    @staticmethod
    def calculate(temperature_c: float, relative_humidity: float, wind_speed_kmh: float = 0, solar_radiation_wm2: float = 0):
        try:
            hi = utilities.heat_index_rothfusz(temperature_c, relative_humidity)
            wbgt = utilities.wbgt(temperature_c, relative_humidity, wind_speed_kmh)
        except Exception:
            hi = None
            wbgt = None
        return {"heat_index": hi, "wbgt": wbgt}

    @staticmethod
    def calculate_batch(data: list):
        return [ThermalIndexService.calculate(**row) for row in data]