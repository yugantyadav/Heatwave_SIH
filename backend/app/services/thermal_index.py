# Thermal index service
# Prefers ml/thermal_engine.py (Lu & Romps 2022 HI + WBGT), then the
# pythermalcomfort package directly, then a self-contained Rothfusz/WBGT
# implementation.
#
# Three bugs hid here until the app ran in a container:
#   1. the ml/ path was built with a fixed "../../..", which lands on / in the
#      flattened image instead of the app root, so the preferred engine was
#      never found;
#   2. pythermalcomfort 3.8 moved heat_index_lu / wbgt from `utilities` to
#      `models` and changed their signatures, so the "fallback" raised;
#   3. every failure was swallowed and returned None, which then let the risk
#      pass silently score a fabricated HI of 35°C.
# Now the last resort is real arithmetic rather than None.
import sys

from app.core.paths import ml_dir

ML_DIR = str(ml_dir())
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

try:
    from thermal_engine import calculate_thermal_indices as _ml_thermal

    _HAVE_ML = True
except Exception:
    _HAVE_ML = False

# pythermalcomfort 3.8 exposes these under `models`; older releases used
# `utilities`, so both spellings are attempted.
try:
    from pythermalcomfort import models as _ptc_models
    from pythermalcomfort.utilities import wet_bulb_tmp as _wet_bulb

    _heat_index_lu = _ptc_models.heat_index_lu
    _wbgt_model = _ptc_models.wbgt
    _HAVE_PTC = True
except Exception:
    _HAVE_PTC = False


def _rothfusz_hi(t_c: float, rh: float) -> float:
    """Rothfusz regression (°F), returned in °C.

    Self-contained so a value always exists even if both libraries are
    unavailable. Mirrors scripts/ingest_weather.py's fallback."""
    t_f = t_c * 9 / 5 + 32
    hi_f = (
        -42.379
        + 2.04901523 * t_f
        + 10.14333127 * rh
        - 0.22475541 * t_f * rh
        - 0.00683783 * t_f * t_f
        - 0.05481717 * rh * rh
        + 0.00122874 * t_f * t_f * rh
        + 0.00085282 * t_f * rh * rh
        - 0.00000199 * t_f * t_f * rh * rh
    )
    return round((hi_f - 32) * 5 / 9, 1)


def _rothfusz_wbgt(t_c: float, rh: float) -> float:
    """Solar WBGT approximation from air temp and humidity."""
    import math

    wb = round(
        0.7 * (
            t_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
            + math.atan(t_c + rh)
            - math.atan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
            - 4.686035
        ),
        1,
    )
    return wb


def _ptc_thermal(temperature_c: float, relative_humidity: float):
    """Lu & Romps HI + outdoor WBGT straight from pythermalcomfort."""
    hi = float(_heat_index_lu(tdb=temperature_c, rh=relative_humidity).hi)
    wet_bulb = float(_wet_bulb(tdb=temperature_c, rh=relative_humidity))
    # Prototype fallback: without a measured globe temperature, air temperature
    # stands in (same assumption as ml/thermal_engine.py).
    wb = float(_wbgt_model(twb=wet_bulb, tg=temperature_c, tdb=temperature_c,
                           with_solar_load=True).wbgt)
    return hi, wb


class ThermalIndexService:
    @staticmethod
    def calculate(temperature_c: float, relative_humidity: float, wind_speed_kmh: float = 0, solar_radiation_wm2: float = 0):
        if _HAVE_ML:
            try:
                out = _ml_thermal(temperature=temperature_c, humidity=relative_humidity)
                return {
                    "heat_index": round(float(out.get("heat_index")), 1),
                    "wbgt": round(float(out.get("wbgt")), 1),
                    "source": "ml/thermal_engine.py",
                }
            except Exception:
                pass
        if _HAVE_PTC:
            try:
                hi, wb = _ptc_thermal(temperature_c, relative_humidity)
                return {"heat_index": round(hi, 1), "wbgt": round(wb, 1),
                        "source": "pythermalcomfort-3.8"}
            except Exception:
                pass
        # Never return None: a missing HI/WBGT makes the risk pass substitute a
        # fabricated value, which is worse than an approximation.
        return {
            "heat_index": _rothfusz_hi(temperature_c, relative_humidity),
            "wbgt": _rothfusz_wbgt(temperature_c, relative_humidity),
            "source": "rothfusz-internal",
        }

    @staticmethod
    def calculate_batch(data: list):
        return [ThermalIndexService.calculate(**row) for row in data]
