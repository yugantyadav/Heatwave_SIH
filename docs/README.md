# Documentation

Project documentation for the Heatwave Early Warning System hackathon submission.

## Project Overview

**Extreme Heatwave Early Warning & Human Thermal Stress Index**
- **Problem Statement**: 26083
- **Timeline**: 14 days (2 weeks)
- **Demo city**: Mumbai (MCGM ward boundaries + ward-level census/demographic data)
- **Team**: 6 roles (R1-R6)

## Deliverables Checklist

- [ ] Working thermal stress engine (HI + WBGT) with cited methodology
- [ ] Mortality/hospitalization risk scoring with cited epidemiological basis
- [ ] Live GIS dashboard with real Mumbai ward data, color-coded risk
- [ ] 3–5 day forecast view
- [ ] Admin panel with threshold config + one-click heat action plan trigger
- [ ] Working SMS/WhatsApp alert demo (sandboxed)
- [ ] Data provenance slide (real vs. modeled data, clearly labeled)
- [ ] Pitch deck + demo script
- [ ] Pre-recorded fallback demo video

## 14-Day Build Flow

### Days 1–2 — Research & Setup
- All: Finalize scope, confirm Mumbai + 3–5 target wards for the demo
- R6: Source and download all datasets (weather, ward shapefiles, demographic, epidemiological coefficients)
- R1: Install/test `pythermalcomfort`, validate HI/WBGT against reference tables
- R2: Research and document the mortality risk-scoring formula, get R6 to sanity-check sources
- R3: Set up FastAPI skeleton, PostGIS schema draft
- R4: Set up React+Vite+Leaflet skeleton, get a static Mumbai ward map rendering
- R5: Set up shared repo, CI basics, Twilio/WhatsApp sandbox accounts

### Days 3–4 — Data Pipeline & Schema
- R1: Build weather ingestion pipeline → clean structured dataset per ward
- R2: Build demographic dataset per ward, draft the risk formula in code
- R3: Finalize PostGIS schema (wards, weather_readings, risk_scores, alerts), seed with ward polygons
- R4: Load real ward GeoJSON into the Leaflet map, style base choropleth
- R5: Start scripting the Twilio/WhatsApp test send (isolated, not yet connected to backend)
- R6: Draft the "data provenance" slide — what's real, what's modeled

### Days 5–7 — Core Engine + Backend API
- R1: Finalize HI + WBGT calculation service, expose as a callable function/module
- R2: Finalize mortality risk model, output a risk category (Low/Moderate/High/Severe) per ward
- R3: Build API endpoints: `GET /wards`, `GET /wards/{id}/risk`, `GET /forecast/{ward_id}`, `POST /thresholds`
- R3+R1+R2: Integrate the thermal + mortality engines into the backend's scheduled job
- R5: Begin connecting the alert trigger logic to the Twilio/WhatsApp sandbox
- R6: Validate the mid-build output against known heatwave events (sanity check)

### Days 8–9 — Frontend Dashboard Build
- R4: Wire dashboard to live backend API — ward colors reflect real computed risk
- R4: Build the 3–5 day forecast timeline component
- R4: Build admin panel (threshold editor, advisory template editor)
- R3: Support R4 with any missing endpoints, fix data-shape mismatches
- R6: Start building the pitch deck structure, gather visuals

### Days 10–11 — Alert Dispatch Integration
- R5: Fully connect threshold-crossing → alert queue → Twilio SMS / WhatsApp send
- R5+R3: Add an alert log table + admin view of sent alerts
- R4: Add a "trigger heat action plan" one-click button in the admin panel wired to R5's dispatch
- R2: Tune risk thresholds against realistic Mumbai heatwave scenarios

### Days 12–13 — Integration Testing & Polish
- All: Full end-to-end run-through — weather in, map + alert out
- R3+R5: Fix integration bugs, handle edge cases (missing data, API failures)
- R4: UI polish, responsive check, loading states
- R6: Finalize pitch deck, write the demo script, record a fallback video of a full working run
- R1+R2: Prepare 1–2 slides explaining the science clearly (formulas, sources) for judge Q&A

### Day 14 — Final Demo Prep
- All: Full dry run of the live demo + fallback video as backup
- R6: Lead rehearsal, assign who answers which likely judge question
- R5: Final deployment check — everything live and stable
- Buffer time for last-minute fixes

## Judge Q&A Readiness

### Common Questions & Approved Answers

**"How accurate is your mortality prediction?"**
→ Be upfront: it's a risk-scoring model grounded in published relative-risk coefficients (Ahmedabad Heat Action Plan studies, Gasparrini et al. 2015 Lancet), not a Mumbai-specific trained model, since ward-level mortality data isn't publicly available at that granularity.

**"Is this real SMS capability?"**
→ Sandboxed Twilio/WhatsApp demo; production deployment would need telecom/WhatsApp Business API approval, which is a post-hackathon integration step.

**"Why HI + WBGT and not UTCI?"**
→ UTCI is the most physiologically complete but computationally heavier; HI + WBGT cover the "quick public alert" and "occupational/outdoor worker risk" use cases directly relevant to the problem statement's stated goals, and UTCI is a stated roadmap item.

## Data Sources

### Weather
- **Open-Meteo API** (free, forecast + historical)
- **IMD API** / **ERA5 reanalysis** (historical)

### Ward Boundaries
- **MCGM open data portal** or **OpenStreetMap** ward boundaries for Mumbai
- **Overpass API** for fetching GeoJSON

### Demographics
- **Census 2011** ward-level data (elderly %)
- **Economic Survey** (outdoor worker density proxy)

### Mortality / Health
- **Ahmedabad Heat Action Plan** published studies (used for risk coefficients, not raw Mumbai data)
- **NCDC heat surveillance reports**
- **Transparent substitution**: "Ahmedabad coefficients used as proxy for Mumbai; ward-level Mumbai mortality data not publicly available"

### Risk Coefficients Source
- Ahmedabad Heat Action Plan studies (Ahmedabad Municipal Corporation + IIPH)
- NCDC heat surveillance reports
- Gasparrini et al. (2015) "Mortality risk attributable to high and low ambient temperature", The Lancet

## Data Provenance

### What's Real
- MCGM ward boundaries (public GIS data)
- Census 2011 demographic data (public domain)
- Open-Meteo weather data (free, real-time)
- Published epidemiological coefficients (peer-reviewed studies)

### What's Modeled/Simulated
- Actual mortality numbers for Mumbai wards (not publicly granular)
- Real-time weather forecasts (Open-Meteo model outputs)
- Twilio/WhatsApp sandbox sends (test mode, not production)
- Exact heat index/WBGT values at ward centroid (approximate)

### Provenance Slide Template
- Left column: "Real Data" — ward shapes, elderly %, historical coefficients
- Right column: "Modeled/Simulated" — risk scores, forecast values, alert dispatch
- clearly labeled: "This is a hackathon prototype, not a production system"

## Project Structure

```
/Heatwave/
├── .gitignore
├── frontend/            # React + Vite + Leaflet dashboard
│   └── README.md
├── backend/             # FastAPI + PostGIS service
│   └── README.md
├── ml/                  # Thermal indices + risk model
│   └── README.md
├── docs/                # Project documentation & pitch materials
│   └── (pitch deck, demo script, data provenance slide)
├── scripts/             # Data ingestion & seeding utilities
│   └── README.md
└── pyproject.toml       # Root package config (optional)
```

## Quick Start (Localhost)

```bash
# 1. Clone & setup
git clone <repo-url>
cd Heatwave

# 2. Start services
brew services start postgresql@16  # or postgresql@17
brew services start redis

# 3. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with credentials
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Frontend
cd ../frontend
npm install
npm run dev -- --host 0.0.0.0

# 5. Seed data
cd ../scripts
python seed_wards.py
python ingest_weather.py

# 5. Access
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

## Role Responsibilities Summary

| Role | Focus | Key Deliverable |
|------|-------|-----------------|
| R1 | Thermal Stress Engine | HI + WBGT calculations, pythermalcomfort validation |
| R2 | Mortality Risk Model | Epidemiological risk scoring, Ahmedabad HAP coefficients |
| R3 | Backend Engineer | FastAPI, PostGIS schema, Celery scheduled jobs |
| R4 | Frontend Engineer | React/Leaflet dashboard, forecast timeline, admin panel |
| R5 | Integration Engineer | ML→backend→frontend pipeline, Twilio/WA sandbox, deployment |
| R6 | Domain/Research Lead | Data sourcing, pitch deck, judge Q&A prep, data provenance |

## Additional Resources

- **pythermalcomfort documentation**: https://pythermalcomfort.readthedocs.io/
- **Ahmedabad Heat Action Plan**: https://ahmedabadapda.org/
- **Open-Meteo API**: https://open-meteo.com/api
- **Overpass Turbo** (for OSM ward queries): https://overpass-turbo.eu/
- **Leaflet.js documentation**: https://leafletjs.com/reference.html
- **Recharts** (React charting): https://recharts.org/