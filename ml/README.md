# Machine Learning (Thermal Stress & Risk Model)

The ML component of Heatwave EWS provides thermal stress index calculations and mortality risk scoring — all based on peer-reviewed epidemiology, not black-box ML models.

## Thermal Stress Engine (HI + WBGT)

### Library: `pythermalcomfort` (≥ 2.6.0)

- **Citation**: Tartarini, F., & Schiavon, S. (2020). pythermalcomfort: A Python package for thermal comfort research. SoftwareX, 12, 100578.

### Heat Index (HI)
- **Equation**: Rothfusz (1990) NWS regression
- **Reference**: Rothfusz, L.P. (1990). "The Heat Index Equation". NWS Southern Region Technical Attachment SR/SSD 90-23
- **Inputs**: Temperature (°C), Relative Humidity (%)
- **Output**: "Feels like" temperature in °C
- **Risk thresholds**: Low (<27°C), Moderate (27-32°C), High (32-41°C), Severe (>41°C)

### Wet Bulb Globe Temperature (WBGT)
- **Equation**: Liljegren et al. (2008) model
- **Reference**: Liljegren, J.I. et al. (2008). "A heat stress index for environmental monitoring"
- **Inputs**: Temperature, RH, wind speed, solar radiation (optional)
- **Output**: WBGT in °C
- **Risk thresholds**: Low (<25°C), Moderate (25-28°C), High (28-31°C), Severe (>31°C)

### Calculation Service
- `thermal_index_service.calculate(temperature_c, relative_humidity, wind_speed_kmh, solar_radiation_wm2?)`
- Returns: `ThermalIndices` dataclass with `heat_index`, `wbgt`, `hi_risk_level`, `wbgt_risk_level`, `overall_risk_category`
- Batch calculation support via `calculate_batch()`

### Validation
- Reference tables from NWS Heat Index and published WBGT studies
- Can be run via: `python ml-engine/thermal_comfort/validation.py`
- Outputs: Per-test pass/fail with calculated vs. expected values

## Mortality Risk Model

### Philosophy: Transparent Epidemiological Scoring — NOT Black-Box ML

**Formula**: `Risk = Base_Risk(thermal_index) × Demographic_Multiplier`

### References (all peer-reviewed)
- **Ahmedabad Heat Action Plan** (IIPH, 2013/2017/2019) — Elderly vulnerability
- **Azhar et al. (2014)** IJERPH — Heat-related mortality in Ahmedabad
- **Gasparrini et al. (2015)** Lancet — Temperature-mortality relationships
- **NCDC Heat Surveillance Reports** — Occupational heat stress

### Coefficients (configurable, documented)
| Coefficient | Value | Source |
|---|---|---|
| Elderly RR per 10% | 1.15 | Azhar et al. 2014 |
| Outdoor worker RR per unit | 1.08 | NCDC/Kjellstrom |
| Base HI threshold (moderate) | 27°C | Ahmedabad HAP |
| Base HI threshold (high) | 32°C | Ahmedabad HAP |
| Base WBGT threshold (moderate) | 25°C | Occupational guidelines |
| Base WBGT threshold (high) | 28°C | Occupational guidelines |

### Risk Scoring Formula
```
1. Base risk from HI curve:
   - <27°C: 10
   - 27-32°C: 25 + linear(hi-27, 32-27)×15
   - 32-41°C: 40 + linear(hi-32, 41-32)×25
   - >41°C: 65 + (hi-41)×1.5 (capped at 95)

2. Base risk from WBGT curve (same structure, different thresholds)

3. Base risk = max(HI_base, WBGT_base)

4. Demographic multiplier:
   = 1 + (elderly_%/100 × elderly_weight) + (outdoor_density × outdoor_worker_weight)

5. Final risk score = base_risk × demographic_multiplier × base_risk_coefficient
   Capped at 100

6. Risk category:
   - <30: Low
   - 30-50: Moderate
   - 50-75: High
   - >75: Severe
```

### Model Interface

```python
from risk_model.mortality_risk import MortalityRiskModel, DEFAULT_COEFFICIENTS

model = MortalityRiskModel(DEFAULT_COEFFICIENTS)
result = model.calculate_risk(
    heat_index=35.0,
    wbgt=29.0,
    elderly_percent=12.5,
    outdoor_worker_density=180.0
)

# result.risk_category -> "high"
# result.final_score -> e.g., 67.3
# result.breakdown contains all component values
```

### Documentation

Full methodology available via: `model.get_methodology()`
Returns dict with: model_type, formula, base_risk_source, demographic_factors, thresholds, transparency notes, limitations

## ML Engine Package

```
ml-engine/
├── pyproject.toml       # Package config (pip install -e .)
├── thermal_comfort/
│   ├── __init__.py
│   ├── indices.py       # HI/WBGT calculator using pythermalcomfort
│   ├── models.py        # Reference documentation (Rothfusz, Liljegren)
│   ├── validation.py    # Reference table validation scripts
│   └── scipy_utf.py     # Numba-accelerated batch calculations (optional)
└── README.md            # This documentation
```

## Key Principles

1. **Transparent**: Every coefficient is documented and configurable
2. **Epidemiological**: Based on published studies, not data-trained models
3. **Defensible**: All judge Q&A answers reference specific studies and equations
4. **Configurable**: Coefficients can be tuned for Mumbai context if data becomes available
5. **Audit-able**: Full formula breakdown stored in database risk_scores table