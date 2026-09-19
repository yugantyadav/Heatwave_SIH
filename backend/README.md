# Backend

FastAPI + PostgreSQL + PostGIS service for the Heatwave Early Warning System.

## Development

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API (to be implemented)

- `GET /api/wards` - List all wards
- `GET /api/risk/wards` - Current risk for all wards
- `GET /api/weather/wards/{id}/forecast` - Weather forecast
- `POST /api/alerts/send` - Send alert
- `GET /api/config/thresholds` - Threshold configuration

## Services (to be implemented)

- Thermal stress engine (HI/WBGT via pythermalcomfort)
- Mortality risk model (epidemiological scoring)
- Weather ingestion (Open-Meteo API)
- Alert dispatch (Twilio/WhatsApp sandbox)