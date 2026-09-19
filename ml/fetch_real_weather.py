import requests
import pandas as pd
import os


# ============================================================
# MUMBAI LOCATION
# ============================================================

LATITUDE = 19.0760
LONGITUDE = 72.8777


# ============================================================
# DOWNLOAD REAL HISTORICAL WEATHER
# ============================================================

def download_weather():

    print()
    print("=" * 60)
    print("       DOWNLOADING REAL MUMBAI WEATHER DATA")
    print("=" * 60)

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {

        "latitude": LATITUDE,

        "longitude": LONGITUDE,

        "start_date": "2024-01-01",

        "end_date": "2025-12-31",

        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "shortwave_radiation"
        ]),

        "temperature_unit": "celsius",

        "wind_speed_unit": "ms",

        "timezone": "Asia/Kolkata"
    }

    print()
    print("Requesting data from Open-Meteo...")

    response = requests.get(
        url,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    print("Weather data received.")

    # --------------------------------------------------------
    # Convert JSON to DataFrame
    # --------------------------------------------------------

    hourly = data["hourly"]

    df = pd.DataFrame(hourly)

    # --------------------------------------------------------
    # Rename columns
    # --------------------------------------------------------

    df = df.rename(columns={

        "time": "timestamp",

        "temperature_2m": "temperature",

        "relative_humidity_2m": "humidity",

        "wind_speed_10m": "wind_speed",

        "shortwave_radiation": "solar_radiation"
    })

    # --------------------------------------------------------
    # Convert timestamp
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    # --------------------------------------------------------
    # Remove missing values
    # --------------------------------------------------------

    df = df.dropna()

    # --------------------------------------------------------
    # Keep only required columns
    # --------------------------------------------------------

    df = df[
        [
            "timestamp",
            "temperature",
            "humidity",
            "wind_speed",
            "solar_radiation"
        ]
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs("data", exist_ok=True)

    output_file = "data/mumbai_weather_real.csv"

    df.to_csv(
        output_file,
        index=False
    )

    # --------------------------------------------------------
    # Display information
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("              DOWNLOAD COMPLETE")
    print("=" * 60)

    print()
    print("Records:", len(df))

    print()
    print("Date range:")
    print(df["timestamp"].min())
    print("to")
    print(df["timestamp"].max())

    print()
    print("Columns:")
    print(df.columns.tolist())

    print()
    print("First 5 records:")
    print(df.head())

    print()
    print("Saved to:")
    print(output_file)

    print()
    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    download_weather()

# ============================================================
# LOAD REAL MUMBAI WEATHER DATA
# ============================================================

def load_weather_data():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'mumbai_weather_real.csv')
    df = pd.read_csv(file_path)
    return df
