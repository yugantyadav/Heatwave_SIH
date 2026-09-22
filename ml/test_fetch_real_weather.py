"""
Integration test for fetch_real_weather.py.

Run with:
    python test_fetch_real_weather.py

By default this does NOT hit the live Open-Meteo API — it only
checks that a previously-downloaded data/mumbai_weather_real.csv
has the shape the rest of the pipeline (ml_anomaly_detector.py,
risk_model.py) expects. This is what should run in CI / before
every demo rehearsal, so you're not dependent on network access
or Open-Meteo being up.

To also test the live download path (slower, needs internet):
    python test_fetch_real_weather.py --live
"""

import os
import sys

import pandas as pd

from fetch_real_weather import download_weather

REQUIRED_COLUMNS = ["timestamp", "temperature", "humidity", "wind_speed", "solar_radiation"]
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "mumbai_weather_real.csv")

failures = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def validate_dataframe(df, source_label):
    check(
        f"{source_label}: has all required columns",
        all(col in df.columns for col in REQUIRED_COLUMNS),
        f"got columns {list(df.columns)}",
    )
    check(f"{source_label}: is not empty", len(df) > 0, f"got {len(df)} rows")

    if all(col in df.columns for col in REQUIRED_COLUMNS):
        check(
            f"{source_label}: temperature values are physically plausible for Mumbai (5-55C)",
            df["temperature"].between(5, 55).all(),
        )
        check(
            f"{source_label}: humidity values are within 0-100%",
            df["humidity"].between(0, 100).all(),
        )
        check(
            f"{source_label}: wind_speed has no negative values",
            (df["wind_speed"] >= 0).all(),
        )
        check(
            f"{source_label}: solar_radiation has no negative values",
            (df["solar_radiation"] >= 0).all(),
        )
        check(
            f"{source_label}: no missing values in required columns",
            not df[REQUIRED_COLUMNS].isnull().any().any(),
        )


print("\n=== FETCH_REAL_WEATHER INTEGRATION TEST ===\n")

if "--live" in sys.argv:
    print("Running LIVE download from Open-Meteo (needs internet)...\n")
    try:
        download_weather()
        check("Live download completed without raising", True)
    except Exception as e:
        check("Live download completed without raising", False, str(e))

if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
    validate_dataframe(df, "data/mumbai_weather_real.csv")
else:
    check(
        "data/mumbai_weather_real.csv exists",
        False,
        "run 'python fetch_real_weather.py' first, or 'python test_fetch_real_weather.py --live'",
    )

print("\n" + "=" * 50)
if failures:
    print(f"RESULT: {len(failures)} check(s) FAILED")
    for f in failures:
        print(f"  - {f}")
    print("=" * 50)
    sys.exit(1)
else:
    print("RESULT: all checks passed")
    print("=" * 50)
    sys.exit(0)
