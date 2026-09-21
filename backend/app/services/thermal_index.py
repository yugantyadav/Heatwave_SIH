# Thermal index service
# Prefers ml/thermal_engine.py (Lu & Romps 2022 HI + WBGT); falls back to
# pythermalcomfort so the API never crashes if the ML package is missing.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))

try:
    from thermal_engine import calculate_thermal_indices as _ml_thermal

    _HAVE_ML = True
except Exception:
    _HAVE_ML = False

from pythermalcomfort import utilities


class ThermalIndexService:
    @staticmethod
    def calculate(temperature_c: float, relative_humidity: float, wind_speed_kmh: float = 0, solar_radiation_wm2: float = 0):
        if _HAVE_ML:
            try:
                out = _ml_thermal(temperature=temperature_c, humidity=relative_humidity)
                hi = float(out.get("heat_index"))
                wbgt = float(out.get("wbgt"))
                return {"heat_index": round(hi, 1), "wbgt": round(wbgt, 1), "source": "ml/thermal_engine.py"}
            except Exception:
                pass
        try:
            hi = utilities.heat_index_rothfusz(temperature_c, relative_humidity)
            wbgt = utilities.wbgt(temperature_c, relative_humidity, wind_speed_kmh)
        except Exception:
            hi = None
            wbgt = None
        return {"heat_index": hi, "wbgt": wbgt, "source": "pythermalcomfort-fallback"}

    @staticmethod
    def calculate_batch(data: list):
        return [ThermalIndexService.calculate(**row) for row in data]