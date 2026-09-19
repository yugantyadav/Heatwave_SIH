# Heatwave EWS - Project Base

## First Edition

This is the base/v1 structure of the Heatwave Early Warning System. Other team members will further develop this repository with:

- Frontend (React + Leaflet dashboard)
- Backend (FastAPI + PostGIS)
- ML models (thermal stress indexing, risk scoring)
- Data pipelines and scripts
- API integrations (Twilio, Open-Meteo, etc.)

## Current Structure

```
heatwave_project/
├── __init__.py     # Package initialization
├── README.md       # Project overview
├── api/            # API route definitions (to be developed)
├── services/       # Business logic services (to be developed)
├── config/         # Configuration management (to be developed)
└── scripts/        # Data ingestion/processing scripts (to be developed)
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt  # To be created

# Run the application
# Backend: uvicorn heatwave_project.api:app --reload
# Frontend: npm run dev (to be set up)
```

## Development Roadmap

1. **R1 (ML Lead)**: Thermal stress engine (HI/WBGT) using pythermalcomfort
2. **R2 (ML Lead)**: Mortality risk model with epidemiological coefficients
3. **R3 (Backend Engineer)**: FastAPI service, PostGIS schema, Celery jobs
4. **R4 (Frontend Engineer)**: React + Leaflet GIS dashboard
5. **R5 (Integration)**: ML → Backend → Frontend pipeline, Twilio/WA alerts
6. **R6 (Domain)**: Data sourcing, provenance, pitch deck, judge Q&A