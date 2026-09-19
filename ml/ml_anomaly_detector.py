import os
import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest


# ============================================================
# LOAD REAL MUMBAI WEATHER DATA
# ============================================================

def load_weather_data():

    file_path = "data/mumbai_weather_real.csv"

    print()
    print("Loading real Mumbai weather data...")

    df = pd.read_csv(
        file_path
    )

    print(
        f"Loaded {len(df)} weather records."
    )

    return df


# ============================================================
# TRAIN ISOLATION FOREST
# ============================================================

def train_anomaly_model(df):

    print()
    print("Training Isolation Forest on REAL data...")

    features = [

        "temperature",

        "humidity",

        "wind_speed",

        "solar_radiation"
    ]

    X = df[features]

    model = IsolationForest(

        n_estimators=200,

        contamination=0.02,

        random_state=42
    )

    model.fit(X)

    print("Training completed.")

    return model, features


# ============================================================
# PREDICT ANOMALY
# ============================================================

def predict_anomaly(

    model,

    features,

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

    prediction = model.predict(X)[0]

    raw_score = model.decision_function(X)[0]

    anomaly = prediction == -1

    anomaly_score = -raw_score

    return anomaly, anomaly_score


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("        REAL MUMBAI HEAT ANOMALY MODEL")
    print("=" * 60)

    # --------------------------------------------------------
    # Load real data
    # --------------------------------------------------------

    df = load_weather_data()

    print()
    print("Dataset preview:")
    print(df.head())

    # --------------------------------------------------------
    # Train model
    # --------------------------------------------------------

    model, features = train_anomaly_model(
        df
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    os.makedirs(
        "models",
        exist_ok=True
    )

    model_path = (
        "models/isolation_forest.joblib"
    )

    joblib.dump(

        {
            "model": model,

            "features": features
        },

        model_path
    )

    print()
    print("Real-data ML model saved to:")

    print(model_path)

    # --------------------------------------------------------
    # Test several conditions
    # --------------------------------------------------------

    test_conditions = [

        {
            "name": "Normal Day",

            "temperature": 30,

            "humidity": 65,

            "wind_speed": 4,

            "solar_radiation": 500
        },

        {
            "name": "Hot Day",

            "temperature": 38,

            "humidity": 75,

            "wind_speed": 3,

            "solar_radiation": 800
        },

        {
            "name": "Extreme Heat",

            "temperature": 43,

            "humidity": 85,

            "wind_speed": 1.5,

            "solar_radiation": 950
        },

        {
            "name": "Extreme Dry Heat",

            "temperature": 45,

            "humidity": 30,

            "wind_speed": 2,

            "solar_radiation": 1000
        }
    ]

    # --------------------------------------------------------
    # Test results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("             ML TEST RESULTS")
    print("=" * 60)

    for condition in test_conditions:

        anomaly, score = predict_anomaly(

            model,

            features,

            condition["temperature"],

            condition["humidity"],

            condition["wind_speed"],

            condition["solar_radiation"]
        )

        print()
        print(
            f"Condition: "
            f"{condition['name']}"
        )

        print("-" * 40)

        print(
            f"Temperature     : "
            f"{condition['temperature']} °C"
        )

        print(
            f"Humidity        : "
            f"{condition['humidity']} %"
        )

        print(
            f"Wind Speed      : "
            f"{condition['wind_speed']} m/s"
        )

        print(
            f"Solar Radiation : "
            f"{condition['solar_radiation']} W/m²"
        )

        if anomaly:

            print(
                "ML Result       : "
                "ANOMALY DETECTED"
            )

        else:

            print(
                "ML Result       : "
                "NORMAL CONDITIONS"
            )

        print(
            f"Anomaly Score   : "
            f"{score:.4f}"
        )

    print()
    print("=" * 60)