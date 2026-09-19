from pythermalcomfort.models import heat_index_lu, wbgt
from pythermalcomfort.utilities import wet_bulb_tmp


# ============================================================
# THERMAL STRESS ENGINE
# ============================================================

def calculate_thermal_indices(
    temperature,
    humidity,
    globe_temperature=None
):
    """
    Calculate thermal stress indicators.

    Parameters
    ----------
    temperature : float
        Air temperature in °C.

    humidity : float
        Relative humidity in %.

    globe_temperature : float, optional
        Globe temperature in °C.

        For a real deployment, this should come from a measured
        or scientifically derived globe temperature.

        If not supplied, air temperature is used as a
        prototype fallback.

    Returns
    -------
    dict
        Heat Index, Wet Bulb Temperature and WBGT.
    """

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if temperature is None:
        raise ValueError("Temperature cannot be None.")

    if humidity is None:
        raise ValueError("Humidity cannot be None.")

    if humidity < 0 or humidity > 100:
        raise ValueError(
            "Humidity must be between 0 and 100%."
        )

    # --------------------------------------------------------
    # 1. HEAT INDEX
    # --------------------------------------------------------
    #
    # Lu & Romps (2022)
    #
    # This is preferred here over Rothfusz because the
    # Rothfusz formulation can produce unrealistic values
    # when extrapolated into extreme conditions.
    #
    # --------------------------------------------------------

    hi_result = heat_index_lu(
        tdb=temperature,
        rh=humidity
    )

    heat_index = hi_result.hi

    # --------------------------------------------------------
    # 2. WET BULB TEMPERATURE
    # --------------------------------------------------------

    wet_bulb = wet_bulb_tmp(
        tdb=temperature,
        rh=humidity
    )

    # --------------------------------------------------------
    # 3. GLOBE TEMPERATURE
    # --------------------------------------------------------

    if globe_temperature is None:

        # Prototype fallback only.
        #
        # In the final system, replace this with measured
        # or properly derived globe temperature.
        globe_temperature = temperature

    # --------------------------------------------------------
    # 4. WBGT
    # --------------------------------------------------------
    #
    # Outdoor WBGT with solar load.
    #
    # twb = natural/wet-bulb temperature
    # tg  = globe temperature
    # tdb = dry-bulb temperature
    #
    # --------------------------------------------------------

    wbgt_result = wbgt(
        twb=wet_bulb,
        tg=globe_temperature,
        tdb=temperature,
        with_solar_load=True
    )

    wbgt_value = wbgt_result.wbgt

    # --------------------------------------------------------
    # 5. RETURN RESULTS
    # --------------------------------------------------------

    return {
        "temperature": float(temperature),

        "humidity": float(humidity),

        "globe_temperature": float(
            globe_temperature
        ),

        "heat_index": float(
            heat_index
        ),

        "wet_bulb": float(
            wet_bulb
        ),

        "wbgt": float(
            wbgt_value
        )
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # Extreme heat test case
    result = calculate_thermal_indices(

        temperature=43,

        humidity=85,

        globe_temperature=45
    )

    print()
    print("=" * 45)
    print("        THERMAL STRESS ENGINE")
    print("=" * 45)

    print()

    print(
        f"Temperature       : "
        f"{result['temperature']} °C"
    )

    print(
        f"Humidity          : "
        f"{result['humidity']} %"
    )

    print(
        f"Globe Temperature : "
        f"{result['globe_temperature']} °C"
    )

    print("-" * 45)

    print(
        f"Heat Index        : "
        f"{result['heat_index']} °C"
    )

    print(
        f"Wet Bulb          : "
        f"{result['wet_bulb']:.2f} °C"
    )

    print(
        f"WBGT              : "
        f"{result['wbgt']} °C"
    )

    print("=" * 45)