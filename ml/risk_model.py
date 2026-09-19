import pandas as pd
import joblib

from thermal_engine import calculate_thermal_indices


# ============================================================
# LOAD TRAINED ML MODEL
# ============================================================

saved_model = joblib.load(
    "models/isolation_forest.joblib"
)

ml_model = saved_model["model"]
features = saved_model["features"]


# ============================================================
# ML ANOMALY DETECTION
# ============================================================

def detect_heat_anomaly(
    temperature,
    humidity,
    wind_speed,
    solar_radiation
):

    weather = pd.DataFrame([{
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "solar_radiation": solar_radiation
    }])

    X = weather[features]

    # Isolation Forest prediction
    prediction = ml_model.predict(X)[0]

    # Raw anomaly score
    raw_score = ml_model.decision_function(X)[0]

    # -1 = anomaly
    #  1 = normal
    anomaly = prediction == -1

    # Convert into an easier 0-100 scale.
    # Higher = more unusual.
    anomaly_score = max(
        0,
        min(100, -raw_score * 100)
    )

    return anomaly, anomaly_score


# ============================================================
# DEMOGRAPHIC VULNERABILITY
# ============================================================

def calculate_vulnerability_score(
    elderly_percent,
    outdoor_worker_percent
):

    # These are configurable prototype weights.
    #
    # They are NOT mortality coefficients.
    # They simply represent vulnerability contribution
    # in the prototype risk model.

    elderly_component = (
        elderly_percent / 100
    ) * 50

    outdoor_worker_component = (
        outdoor_worker_percent / 100
    ) * 50

    vulnerability_score = (
        elderly_component +
        outdoor_worker_component
    )

    return min(100, vulnerability_score)


# ============================================================
# THERMAL STRESS SCORE
# ============================================================

def calculate_thermal_score(
    heat_index,
    wbgt
):

    # Normalize the two thermal indicators.
    #
    # These thresholds are configurable prototype
    # normalization values, not medical thresholds.

    heat_index_score = (
        (heat_index - 27) / (60 - 27)
    ) * 100

    wbgt_score = (
        (wbgt - 18) / (40 - 18)
    ) * 100

    heat_index_score = max(
        0,
        min(100, heat_index_score)
    )

    wbgt_score = max(
        0,
        min(100, wbgt_score)
    )

    thermal_score = (
        heat_index_score * 0.5 +
        wbgt_score * 0.5
    )

    return thermal_score


# ============================================================
# FINAL HEAT-HEALTH RISK SCORE
# ============================================================

def predict_heat_health_risk(
    temperature,
    humidity,
    wind_speed,
    solar_radiation,
    elderly_percent=10,
    outdoor_worker_percent=20,
    globe_temperature=None
):

    # --------------------------------------------------------
    # 1. THERMAL ENGINE
    # --------------------------------------------------------

    thermal = calculate_thermal_indices(
        temperature=temperature,
        humidity=humidity,
        globe_temperature=globe_temperature
    )

    heat_index = thermal["heat_index"]
    wbgt = thermal["wbgt"]

    # --------------------------------------------------------
    # 2. MACHINE LEARNING
    # --------------------------------------------------------

    anomaly, anomaly_score = detect_heat_anomaly(
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        solar_radiation=solar_radiation
    )

    # --------------------------------------------------------
    # 3. THERMAL SCORE
    # --------------------------------------------------------

    thermal_score = calculate_thermal_score(
        heat_index,
        wbgt
    )

    # --------------------------------------------------------
    # 4. VULNERABILITY SCORE
    # --------------------------------------------------------

    vulnerability_score = calculate_vulnerability_score(
        elderly_percent,
        outdoor_worker_percent
    )

    # --------------------------------------------------------
    # 5. FINAL RISK SCORE
    # --------------------------------------------------------

    #
    # Prototype weighting:
    #
    # Thermal stress       = 60%
    # ML anomaly           = 25%
    # Vulnerability        = 15%
    #
    # These weights are configuration parameters for the
    # prototype and should be validated/documented before
    # being presented as scientifically calibrated.
    #

    risk_score = (
        thermal_score * 0.60 +
        anomaly_score * 0.25 +
        vulnerability_score * 0.15
    )

    risk_score = max(
        0,
        min(100, risk_score)
    )

    # --------------------------------------------------------
    # 6. RISK CATEGORY
    # --------------------------------------------------------

    if risk_score < 30:

        risk_level = "LOW"

    elif risk_score < 50:

        risk_level = "MODERATE"

    elif risk_score < 75:

        risk_level = "HIGH"

    else:

        risk_level = "SEVERE"

    # --------------------------------------------------------
    # 7. RETURN RESULT
    # --------------------------------------------------------

    return {

        "temperature": round(
            temperature, 1
        ),

        "humidity": round(
            humidity, 1
        ),

        "wind_speed": round(
            wind_speed, 1
        ),

        "solar_radiation": round(
            solar_radiation, 1
        ),

        "heat_index": round(
            heat_index, 1
        ),

        "wbgt": round(
            wbgt, 1
        ),

        "thermal_score": round(
            thermal_score, 1
        ),

        "anomaly": anomaly,

        "anomaly_score": round(
            anomaly_score, 1
        ),

        "vulnerability_score": round(
            vulnerability_score, 1
        ),

        "risk_score": round(
            risk_score, 1
        ),

        "risk_level": risk_level
    }


# ============================================================
# TEST COMPLETE PIPELINE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("          COMPLETE HEAT-HEALTH RISK MODEL")
    print("=" * 60)

    # --------------------------------------------------------
    # Test Scenario
    # --------------------------------------------------------

    result = predict_heat_health_risk(

        temperature=43,

        humidity=85,

        wind_speed=1.5,

        solar_radiation=950,

        elderly_percent=12,

        outdoor_worker_percent=35,

        globe_temperature=45
    )

    # --------------------------------------------------------
    # Display Results
    # --------------------------------------------------------

    print()
    print("WEATHER CONDITIONS")
    print("-" * 40)

    print(
        f"Temperature       : "
        f"{result['temperature']} °C"
    )

    print(
        f"Humidity          : "
        f"{result['humidity']} %"
    )

    print(
        f"Wind Speed        : "
        f"{result['wind_speed']} m/s"
    )

    print(
        f"Solar Radiation   : "
        f"{result['solar_radiation']} W/m²"
    )

    print()
    print("THERMAL ENGINE")
    print("-" * 40)

    print(
        f"Heat Index        : "
        f"{result['heat_index']} °C"
    )

    print(
        f"WBGT              : "
        f"{result['wbgt']} °C"
    )

    print(
        f"Thermal Score     : "
        f"{result['thermal_score']}"
    )

    print()
    print("MACHINE LEARNING")
    print("-" * 40)

    print(
        f"Anomaly Detected  : "
        f"{result['anomaly']}"
    )

    print(
        f"Anomaly Score     : "
        f"{result['anomaly_score']}"
    )

    print()
    print("POPULATION VULNERABILITY")
    print("-" * 40)

    print(
        f"Vulnerability     : "
        f"{result['vulnerability_score']}"
    )

    print()
    print("FINAL RESULT")
    print("-" * 40)

    print(
        f"Risk Score        : "
        f"{result['risk_score']} / 100"
    )

    print(
        f"Risk Level        : "
        f"{result['risk_level']}"
    )

    print()
    print("=" * 60)