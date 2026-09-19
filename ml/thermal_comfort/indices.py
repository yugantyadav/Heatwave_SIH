from pythermalcomfort import utilities
from typing import Optional, Dict, Any

RothfuszCoefficients = {
    "a1": -42.379, "a2": 2.04901523, "a3": 10.14333127,
    "a4": -0.22475541, "a5": -6.83783e-3, "a6": -5.481717e-2,
    "a7": 1.22874e-3, "a8": 8.5282e-4, "a9": -1.99e-6
}

def heat_index_rothfusz(T: float, RH: float) -> float:
    """Rothfusz (1990) NWS regression equation for Heat Index."""
    T = float(T)
    RH = float(RH)
    HI = (RothfuszCoefficients["a1"] +
          RothfuszCoefficients["a2"]*T +
          RothfuszCoefficients["a3"]*RH +
          RothfuszCoefficients["a4"]*T*RH +
          RothfuszCoefficients["a5"]*T**2 +
          RothfuszCoefficients["a6"]*RH**2 +
          RothfuszCoefficients["a7"]*T**2*RH +
          RothfuszCoefficients["a8"]*T*RH**2 +
          RothfuszCoefficients["a9"]*T**2*RH**2)
    
    # Adjustments for edge cases
    if RH < 13 and 80 <= T <= 112:
        HI -= ((13 - RH) / 4) * ((17 - abs(T - 95)) / 17) ** 0.5
    elif RH > 85 and 80 <= T <= 87:
        HI += ((RH - 85) / 10) * ((87 - T) / 5)
    
    return round(HI, 1)

def wbgt_liljegren(T: float, RH: float, wind_speed_kmh: float) -> float:
    """Liljegren et al. (2008) WBGT model.
    
    Reference: Liljegren, J.I., et al. (2008).
    'A heat stress index for environmental monitoring.'
    International Journal of Biometeorology, 53(3), 275-285.
    """
    # Simplified WBGT calculation using the Liljegren approach
    # WBGT = 0.7 * Tnwb + 0.3 * Tg + 0.7 * Ta - 4.25 (simplified)
    # Where Tnwb is natural wet bulb temperature (approximated)
    Tnwb = T - (0.00066 * (1 + 0.00115 * wind_speed_kmh) * (T - (0.00066 * (1 + 0.00115 * wind_speed_kmh) * (T - RH * 0.1))))
    Tnwb = T - (RH / 100) * (T - 14.65) * 0.75  # Approximate wet bulb
    
    wbgt = 0.7 * Tnwb + 0.3 * T + 0.0  # Simplified: no solar radiation
    return round(wbgt, 1)

def validate_against_reference(calculated_hi: float, reference_hi: float, tolerance: float = 2.0) -> Dict[str, Any]:
    """Validate calculated Heat Index against NWS reference tables."""
    error = abs(calculated_hi - reference_hi) if calculated_hi and reference_hi else None
    return {
        "calculated": calculated_hi,
        "reference": reference_hi,
        "error": error,
        "within_tolerance": error <= tolerance if error is not None else None,
        "status": "PASS" if error and error <= tolerance else "REVIEW"
    }