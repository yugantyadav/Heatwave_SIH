# Machine Learning (Thermal Stress & Risk Model)

## Thermal Stress Engine

- Heat Index (HI) via pythermalcomfort `heat_index_rothfusz`
- Wet Bulb Globe Temperature (WBGT) via pythermalcomfort `wbgt`
- Reference: Rothfusz (1990) NWS equation, Liljegren et al. (2008)

## Mortality Risk Model

- Epidemiological risk scoring (NOT black-box ML)
- Based on Ahmedabad Heat Action Plan coefficients
- Relative risk multipliers for elderly % and outdoor worker density
- Risk categories: Low / Moderate / High / Severe

## Configuration

- All coefficients configurable via `.env`
- Transparent formula stored in database