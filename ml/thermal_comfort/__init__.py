from pythermalcomfort import utilities
from typing import Optional, Dict, Any

def calculate_heat_index(temperature_c: float, relative_humidity: float) -> Optional[float]:
    """Calculate Heat Index using Rothfusz (1990) NWS equation."""
    try:
        return utilities.heat_index_rothfusz(temperature_c, relative_humidity)
    except Exception:
        return None

def calculate_wbgt(temperature_c: float, relative_humidity: float, wind_speed_kmh: float = 0) -> Optional[float]:
    """Calculate Wet Bulb Globe Temperature using Liljegren et al. (2008) model."""
    try:
        return utilities.wbgt(temperature_c, relative_humidity, wind_speed_kmh)
    except Exception:
        return None

def calculate_indices(temperature_c: float, relative_humidity: float, wind_speed_kmh: float = 0, solar_radiation_wm2: float = 0) -> Dict[str, Any]:
    """Calculate both HI and WBGT. Returns dict with heat_index, wbgt, and risk levels."""
    hi = calculate_heat_index(temperature_c, relative_humidity)
    wbgt = calculate_wbgt(temperature_c, relative_humidity, wind_speed_kmh)
    
    hi_risk = _risk_level_hi(hi) if hi else None
    wbgt_risk = _risk_level_wbgt(wbgt) if wbgt else None
    overall = _overall_risk(hi_risk, wbgt_risk)
    
    return {
        "heat_index": hi,
        "wbgt": wbgt,
        "hi_risk_level": hi_risk,
        "wbgt_risk_level": wbgt_risk,
        "overall_risk_category": overall
    }

def _risk_level_hi(hi: float) -> str:
    if hi < 27: return "low"
    elif hi < 32: return "moderate"
    elif hi < 41: return "high"
    else: return "severe"

def _risk_level_wbgt(wbgt: float) -> str:
    if wbgt < 25: return "low"
    elif wbgt < 28: return "moderate"
    elif wbgt < 31: return "high"
    else: return "severe"

def _overall_risk(hi_risk: str, wbgt_risk: str) -> str:
    levels = {"low": 0, "moderate": 1, "high": 2, "severe": 3}
    worst = max(levels.get(hi_risk, 0), levels.get(wbgt_risk, 0))
    return {v: k for k, v in levels.items()}[worst]

__all__ = ["calculate_heat_index", "calculate_wbgt", "calculate_indices"]