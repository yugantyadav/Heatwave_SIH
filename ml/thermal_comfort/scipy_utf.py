"""Numba-accelerated batch calculations for thermal indices."""
from numba import njit
import numpy as np

@njit
def batch_heat_index(temperatures: np.ndarray, humidities: np.ndarray) -> np.ndarray:
    """Numba-accelerated batch Heat Index calculation using Rothfusz equation."""
    results = np.zeros(len(temperatures))
    for i in range(len(temperatures)):
        T = temperatures[i]
        RH = humidities[i]
        HI = (-42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH
              - 6.83783e-3*T**2 - 5.481717e-2*RH**2 + 1.22874e-3*T**2*RH
              + 8.5282e-4*T*RH**2 - 1.99e-6*T**2*RH**2)
        
        # Edge case adjustments
        if RH < 13 and 80 <= T <= 112:
            HI -= ((13 - RH) / 4) * ((17 - abs(T - 95)) / 17) ** 0.5
        elif RH > 85 and 80 <= T <= 87:
            HI += ((RH - 85) / 10) * ((87 - T) / 5)
        
        results[i] = round(HI, 1)
    return results

@njit
def batch_wbgt(temperatures: np.ndarray, humidities: np.ndarray, wind_speeds: np.ndarray) -> np.ndarray:
    """Numba-accelerated batch WBGT calculation."""
    results = np.zeros(len(temperatures))
    for i in range(len(temperatures)):
        T = temperatures[i]
        RH = humidities[i]
        ws = wind_speeds[i]
        Tnwb = T - (RH / 100) * (T - 14.65) * 0.75
        wbgt = 0.7 * Tnwb + 0.3 * T
        results[i] = round(wbgt, 1)
    return results

def compute_all_batch(temperatures: list, humidities: list, wind_speeds: list) -> dict:
    """Compute all thermal indices in batch."""
    import numpy as np
    temps_arr = np.array(temperatures, dtype=np.float64)
    hum_arr = np.array(humidities, dtype=np.float64)
    wind_arr = np.array(wind_speeds, dtype=np.float64)
    
    hi_batch = batch_heat_index(temps_arr, hum_arr)
    wbgt_batch = batch_wbgt(temps_arr, hum_arr, wind_arr)
    
    return {
        "heat_index": hi_batch.tolist(),
        "wbgt": wbgt_batch.tolist(),
        "count": len(temperatures)
    }