from risk_model import predict_heat_health_risk


def get_heat_risk(
    temperature,
    humidity,
    wind_speed,
    solar_radiation,
    elderly_percent=10,
    outdoor_worker_percent=20,
    globe_temperature=None
):
    """
    Main AI/ML interface for the backend.

    Parameters
    ----------
    temperature : float
        Air temperature in °C.

    humidity : float
        Relative humidity in %.

    wind_speed : float
        Wind speed in m/s.

    solar_radiation : float
        Solar radiation in W/m².

    elderly_percent : float
        Percentage of elderly population in the ward.

    outdoor_worker_percent : float
        Percentage of outdoor workers in the ward.

    globe_temperature : float, optional
        Globe temperature in °C.

    Returns
    -------
    dict
        Complete heat-health risk result.
    """

    result = predict_heat_health_risk(

        temperature=temperature,

        humidity=humidity,

        wind_speed=wind_speed,

        solar_radiation=solar_radiation,

        elderly_percent=elderly_percent,

        outdoor_worker_percent=outdoor_worker_percent,

        globe_temperature=globe_temperature
    )

    return result


if __name__ == "__main__":

    result = get_heat_risk(

        temperature=43,

        humidity=85,

        wind_speed=1.5,

        solar_radiation=950,

        elderly_percent=12,

        outdoor_worker_percent=35,

        globe_temperature=45
    )

    print()
    print("=" * 50)
    print("       AI/ML HEAT RISK ENGINE")
    print("=" * 50)

    for key, value in result.items():

        print(
            f"{key:22}: {value}"
        )

    print("=" * 50)