class ThermalIndices:
    """Dataclass for thermal index results."""
    heat_index: Optional[float]
    wbgt: Optional[float]
    hi_risk_level: Optional[str]
    wbgt_risk_level: Optional[str]
    overall_risk_category: Optional[str]

def calculate_batch(data: list) -> list:
    """Calculate thermal indices for multiple data points."""
    results = []
    for row in data:
        result = calculate_indices(
            temperature_c=row["temperature_c"],
            relative_humidity=row["relative_humidity"],
            wind_speed_kmh=row.get("wind_speed_kmh", 0),
            solar_radiation_wm2=row.get("solar_radiation_wm2", 0)
        )
        results.append(result)
    return results