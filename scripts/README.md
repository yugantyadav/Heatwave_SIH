# Scripts

Utility scripts for Heatwave EWS data ingestion and seeding.

## Setup

```bash
cd scripts
pip install -r ../backend/requirements.txt
```

## Available Scripts

### `seed_wards.py`
Seeds 5 demo wards for Mumbai into the database.

```bash
python seed_wards.py
```

### `ingest_weather.py`
Fetches 3-day weather forecast from Open-Meteo for all wards and stores in database.

```bash
python ingest_weather.py
```

Both scripts expect the backend to be running and DATABASE_URL configured in `.env`.