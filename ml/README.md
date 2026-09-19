# Mumbai Extreme Heatwave — AI/ML Engine

## Overview

This module calculates thermal stress, detects unusual weather conditions using
machine learning, incorporates population vulnerability, and produces a
heat-health risk score.

The complete pipeline is:

Weather Data
    ↓
Thermal Engine
    ↓
Heat Index + Wet Bulb + WBGT
    ↓
Isolation Forest
    ↓
Weather Anomaly
    ↓
Population Vulnerability
    ↓
Heat-Health Risk Score
    ↓
LOW / MODERATE / HIGH / SEVERE


============================================================
1. PROJECT STRUCTURE
============================================================

ai_ml/
│
├── ai_engine.py
├── thermal_engine.py
├── ml_anomaly_detector.py
├── risk_model.py
├── fetch_real_weather.py
├── test.py
├── requirements.txt
├── README.md
│
├── models/
│   └── isolation_forest.joblib
│
└── data/
    └── mumbai_weather_real.csv


============================================================
2. FILE DESCRIPTIONS
============================================================

ai_engine.py
------------
Main interface for the backend.

The backend should primarily import:

from ai_engine import get_heat_risk

This function runs the complete AI/ML pipeline.


thermal_engine.py
-----------------
Calculates:

- Heat Index
- Wet-bulb temperature
- WBGT

The calculations use the pythermalcomfort library.


ml_anomaly_detector.py
----------------------
Trains the Isolation Forest machine-learning model.

Features used:

- Temperature
- Relative humidity
- Wind speed
- Solar radiation

The current model is trained using historical Mumbai
weather data downloaded through Open-Meteo.


risk_model.py
-------------
Combines:

- Thermal stress
- ML anomaly
- Population vulnerability

and generates the final risk score and risk category.


fetch_real_weather.py
---------------------
Downloads historical Mumbai weather data and saves it to:

data/mumbai_weather_real.csv


models/isolation_forest.joblib
------------------------------
Serialized trained Isolation Forest model.

This file is loaded by risk_model.py.


requirements.txt
----------------
Contains the Python dependencies required to run
the AI/ML module.


============================================================
3. INSTALLATION
============================================================

From inside the ai_ml folder:

Create the virtual environment:

python -m venv .venv

Activate it on Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt


============================================================
4. DOWNLOAD REAL WEATHER DATA
============================================================

Run:

python fetch_real_weather.py

This downloads historical Mumbai weather data and saves:

data/mumbai_weather_real.csv

Current dataset:

Location:
Mumbai, Maharashtra, India

Period:
2024-01-01 to 2025-12-31

Approximate records:
17,544 hourly records


============================================================
5. TRAIN THE ML MODEL
============================================================

Run:

python ml_anomaly_detector.py

This:

1. Loads the real weather dataset.
2. Selects the ML features.
3. Trains an Isolation Forest.
4. Tests several weather conditions.
5. Saves the trained model.

The trained model is saved to:

models/isolation_forest.joblib


============================================================
6. RUN THE COMPLETE RISK MODEL
============================================================

Run:

python risk_model.py

This combines:

Weather
    ↓
Thermal Engine
    ↓
Isolation Forest
    ↓
Population Vulnerability
    ↓
Risk Score


============================================================
7. MAIN AI/ML INTERFACE
============================================================

The backend should use:

from ai_engine import get_heat_risk

Example:

result = get_heat_risk(
    temperature=38,
    humidity=75,
    wind_speed=3,
    solar_radiation=800,
    elderly_percent=10,
    outdoor_worker_percent=30
)

print(result)


============================================================
8. INPUT PARAMETERS
============================================================

temperature
-----------
Air temperature in degrees Celsius.

Example:

temperature=38


humidity
--------
Relative humidity in percent.

Example:

humidity=75


wind_speed
----------
Wind speed in metres per second.

Example:

wind_speed=3


solar_radiation
---------------
Shortwave solar radiation in watts per square metre.

Example:

solar_radiation=800


elderly_percent
---------------
Percentage of the population classified as elderly
for the relevant geographical area.

Example:

elderly_percent=10


outdoor_worker_percent
----------------------
Percentage of the population considered exposed to
outdoor work.

Example:

outdoor_worker_percent=30


globe_temperature
-----------------
Globe temperature in degrees Celsius.

This is optional in the current prototype.

Example:

globe_temperature=45

For final deployment, globe temperature should come from
a measurement or a scientifically defensible calculation.


============================================================
9. MACHINE LEARNING MODEL
============================================================

Algorithm:

Isolation Forest

Type:

Unsupervised anomaly detection


Features:

- temperature
- humidity
- wind_speed
- solar_radiation


Purpose:

The model learns statistical patterns in historical
weather and identifies observations that are unusual.

The Isolation Forest does NOT directly predict:

- mortality
- deaths
- hospital admissions
- individual medical outcomes


It detects unusual weather conditions.


============================================================
10. THERMAL ENGINE
============================================================

The thermal engine calculates:

- Heat Index
- Wet-bulb temperature
- WBGT


Heat Index
----------

Represents apparent temperature under hot/humid
conditions.

The project currently uses the Lu & Romps Heat Index
implementation available through pythermalcomfort.


Wet-bulb temperature
--------------------

Represents the cooling effect of evaporation under
the specified atmospheric conditions.


WBGT
----

Wet Bulb Globe Temperature is a heat-stress indicator
that incorporates environmental conditions.

For the current outdoor calculation, WBGT uses:

- wet-bulb temperature
- globe temperature
- dry-bulb temperature


IMPORTANT:

The current globe temperature used in testing may be
provided manually.

For final deployment, measured or scientifically
derived globe temperature should be used.


============================================================
11. RISK MODEL
============================================================

The current prototype combines:

Thermal Stress
      +
ML Weather Anomaly
      +
Population Vulnerability
      ↓
Heat-Health Risk Score


Current prototype weighting:

Thermal component        60%

ML anomaly component     25%

Vulnerability component  15%


IMPORTANT:

These are prototype configuration weights.

They are NOT medically validated coefficients.

They should be described as configurable,
evidence-informed prototype parameters.


============================================================
12. RISK CATEGORIES
============================================================

Current prototype classification:

0 - 29
LOW

30 - 49
MODERATE

50 - 74
HIGH

75 - 100
SEVERE


IMPORTANT:

These thresholds are prototype classification
thresholds.

They should not be presented as official medical
or government heat-warning thresholds unless they
are separately validated.


============================================================
13. REAL WEATHER DATA
============================================================

The current ML model is trained using historical
Mumbai weather data obtained through Open-Meteo's
historical weather API.

Variables include:

- Temperature
- Relative humidity
- Wind speed
- Solar radiation


The current dataset covers:

2024-01-01
through
2025-12-31


There are approximately:

17,544 hourly records.


IMPORTANT:

The historical dataset is reanalysis-based data and
should not be described as equivalent to measurements
from one specific Mumbai weather station.


============================================================
14. EPIDEMIOLOGICAL EVIDENCE
============================================================

The broader project can incorporate published
epidemiological evidence to inform vulnerability
and heat-health risk adjustments.

Evidence from other Indian cities, such as Ahmedabad,
must not automatically be treated as Mumbai-specific
mortality coefficients.

When epidemiological evidence is used, document:

1. Original study population
2. Geographic location
3. Temperature definition
4. Exposure period
5. Statistical interpretation
6. Transferability limitations


The preferred description is:

"Evidence-informed heat-health risk scoring"

NOT:

"Mumbai mortality prediction"


============================================================
15. COMPLETE ARCHITECTURE
============================================================

                    WEATHER DATA
                         |
                         v
              +---------------------+
              | Temperature         |
              | Humidity            |
              | Wind Speed          |
              | Solar Radiation     |
              +----------+----------+
                         |
                         v
              +---------------------+
              |   THERMAL ENGINE    |
              |                     |
              | Heat Index          |
              | Wet Bulb            |
              | WBGT                |
              +----------+----------+
                         |
                         v
              +---------------------+
              |   ISOLATION FOREST  |
              |                     |
              | Weather Anomaly      |
              +----------+----------+
                         |
                         v
              +---------------------+
              |    RISK MODEL       |
              |                     |
              | Thermal Stress       |
              | ML Anomaly           |
              | Demographics         |
              | Evidence             |
              +----------+----------+
                         |
                         v
                    RISK SCORE
                         |
                         v
             LOW / MODERATE / HIGH
                    / SEVERE


============================================================
16. BACKEND INTEGRATION
============================================================

The backend imports:

from ai_engine import get_heat_risk


Example:

result = get_heat_risk(
    temperature=38,
    humidity=75,
    wind_speed=3,
    solar_radiation=800,
    elderly_percent=10,
    outdoor_worker_percent=30
)


The backend receives a dictionary containing:

- temperature
- humidity
- wind_speed
- solar_radiation
- heat_index
- wbgt
- thermal_score
- anomaly
- anomaly_score
- vulnerability_score
- risk_score
- risk_level


============================================================
17. FASTAPI EXAMPLE
============================================================

Example FastAPI integration:

from fastapi import FastAPI
from ai_engine import get_heat_risk

app = FastAPI()


@app.post("/heat-risk")
def heat_risk(data: dict):

    result = get_heat_risk(
        temperature=data["temperature"],
        humidity=data["humidity"],
        wind_speed=data["wind_speed"],
        solar_radiation=data["solar_radiation"],
        elderly_percent=data.get(
            "elderly_percent",
            10
        ),
        outdoor_worker_percent=data.get(
            "outdoor_worker_percent",
            20
        ),
        globe_temperature=data.get(
            "globe_temperature"
        )
    )

    return result


============================================================
18. EXAMPLE API REQUEST
============================================================

{
    "temperature": 38,
    "humidity": 75,
    "wind_speed": 3,
    "solar_radiation": 800,
    "elderly_percent": 10,
    "outdoor_worker_percent": 30
}


============================================================
19. EXAMPLE RESPONSE
============================================================

{
    "temperature": 38.0,
    "humidity": 75.0,
    "wind_speed": 3.0,
    "solar_radiation": 800.0,
    "heat_index": 66.7,
    "wbgt": 36.6,
    "thermal_score": 85.2,
    "anomaly": true,
    "anomaly_score": 6.3,
    "vulnerability_score": 20.0,
    "risk_score": 61.5,
    "risk_level": "HIGH"
}


NOTE:

The values above are illustrative.

Actual values must always be obtained by running
get_heat_risk().


============================================================
20. RESPONSIBILITIES
============================================================

AI/ML TEAM
----------

Responsible for:

- Weather preprocessing
- Thermal calculations
- Heat Index
- WBGT
- Wet-bulb calculation
- Isolation Forest
- Anomaly detection
- Vulnerability scoring
- Risk scoring
- Trained model
- AI/ML interface


BACKEND TEAM
------------

Responsible for:

- FastAPI
- PostgreSQL/PostGIS
- Mumbai ward boundaries
- Ward demographic data
- Live weather ingestion
- API endpoints
- Scheduling
- Alert system
- Communication with frontend


FRONTEND TEAM
-------------

Responsible for:

- Mumbai map
- Ward visualization
- Risk colors
- Heat-health dashboard
- Charts
- User interface
- Alert display


============================================================
21. CURRENT AI/ML STATUS
============================================================

Python environment             DONE

Pandas preprocessing            DONE

Real weather dataset            DONE

Thermal Engine                  DONE

Heat Index                      DONE

Wet-bulb calculation            DONE

WBGT                            DONE

Isolation Forest                DONE

Real-data model training        DONE

Model serialization             DONE

Risk model                      DONE

Backend interface               DONE

Requirements file               DONE

Documentation                   DONE


============================================================
22. IMPORTANT LIMITATIONS
============================================================

This system is a hackathon prototype.

The following should not be claimed:

- Direct mortality prediction
- Individual medical prediction
- Medically validated diagnosis
- Official government warning classification
- Exact prediction of deaths
- Exact prediction of hospital admissions


The system should instead be described as:

"An AI-assisted heat-health risk assessment and
early-warning system."


The ML component detects statistically unusual
weather conditions.

The thermal engine calculates environmental heat
stress.

The risk model combines thermal stress, ML anomaly,
and population vulnerability into a heat-health
risk indicator.


============================================================
23. FINAL PIPELINE
============================================================

Real Mumbai Weather
        ↓
Temperature
Humidity
Wind Speed
Solar Radiation
        ↓
Thermal Engine
        ↓
Heat Index
Wet Bulb
WBGT
        ↓
Isolation Forest
        ↓
Weather Anomaly
        ↓
Population Vulnerability
        ↓
Evidence-Informed Risk Model
        ↓
Heat-Health Risk Score
        ↓
LOW / MODERATE / HIGH / SEVERE


============================================================
24. CORE BACKEND FUNCTION
============================================================

The main function the backend should use is:

from ai_engine import get_heat_risk


Example:

result = get_heat_risk(
    temperature=38,
    humidity=75,
    wind_speed=3,
    solar_radiation=800,
    elderly_percent=10,
    outdoor_worker_percent=30
)


The backend should treat the returned result as
environmental heat-health risk information and not
as an individual medical prediction.


============================================================
END
============================================================