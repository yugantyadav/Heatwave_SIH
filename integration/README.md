# Integration Module

Full-stack integration for Heatwave EWS — localhost-only demo mode.

## Architecture Overview

```
Frontend (React + Vite + Leaflet)      ←→  Backend (FastAPI)
     │                                    │
     ▼                                    ▼
  http://localhost:5173                  http://localhost:8000
         │                                    │
         └────────────────────────────────────┘
                  REST API: /api/...

## API Endpoints (Localhost Only)

### Ward & Risk
- `GET /api/wards` — List all wards
- `GET /api/wards/geojson` — GeoJSON for map
- `GET /api/wards/{ward_id}` — Ward details
- `GET /api/risk/wards` — Current risk for all wards (map)
- `GET /api/risk/wards/{ward_id}` — Ward-specific risk

### Weather
- `GET /api/weather/wards/{ward_id}/current` — Current weather
- `GET /api/weather/wards/{ward_id}/forecast` — 3-5 day forecast

### Alerts
- `POST /api/alerts/send` — Send manual alert
- `POST /api/alerts/trigger` — Trigger heat action plan

### Config
- `GET /api/config/thresholds` — Current thresholds
- `GET /api/config/advisories` — Advisory templates

## Local Development Flow

1. **Backend**: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
2. **Frontend**: `cd frontend && npm run dev -- --host 0.0.0.0`
3. **Seed Data**: `cd scripts && python seed_wards.py`
4. **Ingest Weather**: `cd scripts && python ingest_weather.py`

## Demo Features (Sandbox Mode)
- ✅ Thermal stress engine (HI + WBGT) via pythermalcomfort
- ✅ Mortality risk scoring with epidemiological coefficients
- ✅ Choropleth ward map with risk coloring
- ✅ 3-day forecast view
- ✅ Admin panel for threshold/config editing
- ⚠️ SMS/WhatsApp sandbox (test sends only, not production)

## Troubleshooting
- Ensure PostgreSQL + PostGIS are running
- Verify `.env` has correct DATABASE_URL
- Check CORS config if frontend can't reach backend
- API docs available at `http://localhost:8000/docs`