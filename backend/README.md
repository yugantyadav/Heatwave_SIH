# Backend

FastAPI + PostgreSQL + PostGIS service for the Heatwave Early Warning System.

## Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point + lifespan (DB init)
│   ├── core/              # Configuration (settings via pydantic-settings)
│   │   └── config.py        # Settings class with .env support
│   ├── db/                # Database session management
│   │   └── session.py       # Async engine, get_db dependency
│   ├── models/            # SQLAlchemy ORM models (wards, weather, risk, alerts, config)
│   │   ├── ward.py
│   │   ├── weather.py
│   │   ├── risk.py
│   │   ├── alert.py
│   │   ├── config.py
│   │   └── __init__.py
│   ├── schemas/           # Pydantic request/response models
│   │   ├── ward.py
│   │   ├── weather.py
│   │   ├── risk.py
│   │   ├── alert.py
│   │   ├── config.py
│   │   └── __init__.py
│   ├── services/          # Business logic
│   │   ├── thermal_index.py # HI/WBGT via pythermalcomfort
│   │   ├── risk_model.py  # Epidemiological risk scoring
│   │   ├── weather.py     # Open-Meteo API client
│   │   └── alerts.py      # Twilio/WhatsApp sandbox integration
│   ├── api/               # FastAPI route handlers
│   │   ├── wards.py
│   │   ├── risk.py
│   │   ├── weather.py
│   │   ├── alerts.py
│   │   └── config.py
│   └── tasks/             # Celery tasks (forecast refresh, risk computation, alert triggering)
│       ├── celery_app.py
│       ├── weather_tasks.py
│       ├── risk_tasks.py
│       └── alert_tasks.py
├── migrations/            # Alembic database migrations
│   ├── env.py
│   └── 001_initial_schema.sql
├── .env.example           # Environment variable templates
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Package configuration
├── Dockerfile             # Docker deployment config
└── alembic.ini            # Alembic configuration
```

## Development

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install package in editable mode
pip install -e .

# 4. Set up environment
cp .env.example .env
# Edit .env with your credentials (Twilio, WhatsApp sandbox, DB params)

# 5. Initialize database
#    - Start PostgreSQL with PostGIS
#    - Run migrations: alembic upgrade head

# 6. Run the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. API documentation available at:
#    http://localhost:8000/docs
#    http://localhost:8000/health
```

## Key Features

- **PostgreSQL + PostGIS** for spatial ward data and geometry queries
- **Async SQLAlchemy** with asyncpg for non-blocking database operations
- **FastAPI** with automatic OpenAPI docs and validation
- **Pydantic models** for request/response validation
- **Celery + Redis** for background task scheduling (forecast refresh every 6 hrs)
- **Thermal engine** using pythermalcomfort (HI via Rothfusz, WBGT via Liljegren)
- **Epidemiological risk scoring** based on Ahmedabad HAP coefficients (NOT ML black-box)
- **Alert system** with Twilio SMS + WhatsApp Cloud API (sandboxed demo mode)
- **CORS configured** for localhost frontend development
- **Environment-based configuration** via pydantic-settings

## Routes Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/wards` | List all wards with optional zone filter |
| GET | `/api/wards/geojson` | GeoJSON for map rendering |
| GET | `/api/wards/{id}` | Single ward details |
| GET | `/api/risk/wards` | Current risk for all wards (map choropleth) |
| GET | `/api/risk/wards/{id}` | Ward-specific risk + forecast |
| GET | `/api/weather/wards/{id}/current` | Current weather conditions |
| GET | `/api/weather/wards/{id}/forecast` | 3-5 day weather forecast |
| POST | `/api/alerts/send` | Send manual alert |
| POST | `/api/alerts/trigger` | Trigger heat action plan |
| GET | `/api/config/thresholds` | Current threshold configuration |
| GET | `/api/config/advisories` | Advisory templates by risk category |

## Database Schema

Core tables:
- `wards` - Mumbai ward polygons (PostGIS geometry), demographics
- `weather_readings` - Historical + forecast weather data
- `risk_scores` - Computed risk per ward per timestamp
- `alerts` - Sent alerts with status and external IDs
- `threshold_configs` - Configurable HI/WBGT thresholds
- `advisory_templates` - SMS/WhatsApp messages per risk level

## Configuration

`.env` file keys:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis for Celery broker/backoff
- `OPEN_METEO_API_KEY` - (free, often empty for basic use)
- `TWILIO_*` - Sandbox SMS credentials
- `WHATSAPP_*` - Sandbox WhatsApp credentials
- `ENVIRONMENT` - development/production
- `FORECAST_REFRESH_HOURS` - How often to refresh forecasts
- Threshold values (HI low/moderate/high/severe, WBGT equivalents)
- Demographic weights (elderly, outdoor worker)