"""
ML Engine test suite.

Run with:
    python test.py

This validates three things, in order:
1. Thermal engine outputs are physically sane and roughly match
   published reference values (catches formula/unit bugs).
2. The end-to-end risk pipeline (predict_heat_health_risk) is
   discriminative across a range of real Mumbai conditions — i.e.
   a mild day and an extreme day must NOT get the same score.
   This directly guards against the heat-index saturation bug
   found in this repo (see risk_model.py comments).
3. The Isolation Forest anomaly model loads and returns a
   prediction end-to-end using the real trained model file.

This is a lightweight smoke-test script, not a pytest suite, so it
can be run with zero extra dependencies during a hackathon demo.
"""

import sys

from thermal_engine import calculate_thermal_indices
from risk_model import predict_heat_health_risk, detect_heat_anomaly


PASS = "PASS"
FAIL = "FAIL"

failures = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


# ============================================================
# 1. THERMAL ENGINE — reference value sanity checks
# ============================================================
# These are NOT exact reference table lookups (Lu & Romps differs
# from the old NWS Rothfusz tables), they are sanity bounds: mild
# conditions should stay mild, extreme conditions should read high,
# and nothing should return an impossible value (negative, NaN, or
# absurdly out of range).

print("\n=== 1. THERMAL ENGINE ===\n")

mild = calculate_thermal_indices(temperature=28, humidity=50)
check(
    "Mild day (28C/50%RH) heat index stays close to air temp",
    25 <= mild["heat_index"] <= 32,
    f"got {mild['heat_index']}",
)

hot = calculate_thermal_indices(temperature=40, humidity=80, globe_temperature=42)
check(
    "Hot humid day (40C/80%RH) heat index is well above air temp",
    hot["heat_index"] > 60,
    f"got {hot['heat_index']}",
)
check(
    "Hot humid day WBGT is in the IMD 'severe heat wave' outdoor-danger band",
    32 <= hot["wbgt"] <= 46,
    f"got {hot['wbgt']}",
)

try:
    calculate_thermal_indices(temperature=40, humidity=150)
    check("Rejects invalid humidity (>100%)", False)
except ValueError:
    check("Rejects invalid humidity (>100%)", True)


# ============================================================
# 2. RISK PIPELINE — must be discriminative, not saturated
# ============================================================
# This is the critical regression test: every step must produce a
# STRICTLY increasing risk score as conditions worsen. If any step
# is flat, the normalization has saturated again.

print("\n=== 2. RISK PIPELINE DISCRIMINATION ===\n")

scenarios = [
    ("Mild",         30, 60, 3.0, 500),
    ("Warm",         35, 65, 3.0, 700),
    ("Hot",          38, 75, 2.5, 800),
    ("Very Hot",     40, 80, 2.0, 900),
    ("Extreme",      43, 85, 1.5, 950),
]

scores = []
for name, t, h, w, s in scenarios:
    result = predict_heat_health_risk(
        temperature=t, humidity=h, wind_speed=w, solar_radiation=s,
        globe_temperature=t + 2,
    )
    scores.append(result["risk_score"])
    print(f"  {name:10s} (T={t}C RH={h}%) -> risk_score={result['risk_score']:5.1f}  level={result['risk_level']}")

check(
    "Risk score strictly increases as conditions worsen (no saturation)",
    all(scores[i] < scores[i + 1] for i in range(len(scores) - 1)),
    f"scores were {scores}",
)
check(
    "Mildest scenario classifies as LOW or MODERATE",
    scores[0] < 50,
)
check(
    "Most extreme scenario classifies as HIGH or SEVERE",
    scores[-1] >= 50,
)


# ============================================================
# 3. ANOMALY MODEL — loads and runs end-to-end
# ============================================================

print("\n=== 3. ANOMALY MODEL ===\n")

try:
    anomaly, score = detect_heat_anomaly(
        temperature=43, humidity=85, wind_speed=1.5, solar_radiation=950
    )
    check("Isolation Forest model loads and predicts without error", True)
    check(
        "Anomaly score is a finite number in [0, 100]",
        0 <= score <= 100,
        f"got {score}",
    )
    print(f"  Extreme scenario -> anomaly={anomaly}, score={score:.1f}")
except FileNotFoundError:
    check(
        "Isolation Forest model file exists (models/isolation_forest.joblib)",
        False,
        "run ml_anomaly_detector.py first to train and save the model",
    )


# ============================================================
# SUMMARY
# ============================================================

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
