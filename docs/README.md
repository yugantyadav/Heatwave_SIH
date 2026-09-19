# Documentation

Project documentation for the Heatwave Early Warning System hackathon submission.

## Project Overview

- **Problem Statement**: 26083
- **Timeline**: 14 days (2 weeks)
- **Demo city**: Mumbai (5 demo wards: 1, 2, 3, 4, 5)
- **Team**: 6 roles (R1-R6)

## Deliverables

- Thermal stress engine (HI + WBGT)
- Mortality/hospitalization risk scoring
- Live GIS dashboard with Mumbai ward data
- 3-5 day forecast view
- Admin panel with threshold config + alert trigger
- SMS/WhatsApp alert demo (sandboxed)
- Data provenance slide (real vs modeled)
- Pitch deck + demo script
- Pre-recorded fallback video

## 14-Day Build Flow

### Days 1-2: Research & Setup (R6 leads)
### Days 3-4: Data Pipeline & Schema (R6, R3)
### Days 5-7: Core Engine + Backend API (R1, R2, R3)
### Days 8-9: Frontend Dashboard Build (R4, R3)
### Days 10-11: Alert Dispatch Integration (R5, R2)
### Days 12-13: Integration Testing & Polish (All)
### Day 14: Final Demo Prep (All)

## Judge Q&A Readiness

**"How accurate is your mortality prediction?"**
→ It's a risk-scoring model grounded in published relative-risk coefficients (Ahmedabad Heat Action Plan studies, Gasparrini et al. 2015 Lancet), not a Mumbai-specific trained model, since ward-level mortality data isn't publicly available at that granularity.

**"Is this real SMS capability?"**
→ Sandboxed Twilio/WhatsApp demo; production deployment would need telecom/WhatsApp Business API approval.

**"Why HI + WBGT and not UTCI?"**
→ UTCI is computationally heavier; HI + WBGT cover public alert + occupational worker risk use cases directly relevant to the problem statement.

## Data Sources

### Weather Data — OPEN-METEO API (Free, No Key)
- **URL**: `https://api.open-meteo.com/v1/forecast?latitude=19.09&longitude=72.87&hourly=temperature_2m,relative_humidity_2m,precipitation,weathercode&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Asia/Kolkata&forecast_days=5`
- **Mumbai coordinates**: 19.086°N, 72.853°E
- **Fields returned**: temperature_2m (°C), relative_humidity_2m (%), precipitation (mm), weathercode (WMO code)
- **Provenance**: REAL — live weather forecast data from a global numerical model
- **Status**: ✅ Verified working, returns 5-day hourly + daily forecasts

### Mumbai Ward Boundaries — OpenStreetMap / Overpass API
- **API endpoint**: `https://overpass-api.de/api/interpreter`
- **Query type**: Relation/admin_level=11 for Mumbai wards
- **Fallback**: MCGM open data portal for official ward shapefiles
- **Status**: ⚠️ Overpass returned 406 error — MCGM shapefiles preferred
- **Provenance**: REAL — official administrative boundaries

### Demographic Data — Census 2011 (Mumbai Ward-wise)
- **Source**: https://data.opencity.in/dataset/mumbai-ward-wise-census-data
- **Data fields**: Ward Code, Total Population, Total Males, Total Females, SC Population, ST Population, Ward Name
- **Coverage**: Mumbai City wards 1-9 + Mumbai Suburban wards 10-24
- **Format**: CSV download available
- **Mumbai City Population 2011**: 3,085,411 (Mumbai City district)
- **Greater Mumbai Population 2011**: 18,414,288 (Greater Mumbai)
- **Overall Elderly % (60+)**: 8.57% (India-wide 2011 Census)
- **Status**: ✅ Available for download, ward-level CSV data

### Epidemiological Risk Coefficients

#### Source 1: Gasparrini et al. 2015 (The Lancet)
- **Full citation**: Gasparrini, A., Guo, Y., Hashizume, M., et al. (2015). "Mortality risk attributable to high and low ambient temperature: a multicountry observational study." The Lancet, 386(9991), 369-375.
- **DOI**: 10.1016/S0140-6736(14)62114-0
- **Key findings**:
  - 7.71% of mortality attributable to non-optimum temperature (95% eCI 7.43-7.91)
  - 6.66% from moderate cold (95% eCI 6.41-6.86)
  - 0.42% from moderate heat (95% eCI 0.39-0.44)
  - Extreme cold/hot: 0.86% of total mortality (95% eCI 0.84-0.87)
  - Optimum/MTT (minimum mortality temperature): varies by region, tropical areas ~60th-80th percentile
  - Risk escalates quickly and non-linearly at high temperatures
  - 384 locations across 13 countries analyzed
- **Cited by**: 3,661+ citations as of 2026
- **Provenance**: REAL — peer-reviewed published study

#### Source 2: Ahmedabad Heat Action Plan (AMC/IIPH/NRDC)
- **First HAP in South Asia**: Launched 2013
- **Partners**: Ahmedabad Municipal Corporation (AMC), Indian Institute of Public Health-Gandhinagar (IIPH), Natural Resources Defense Council (NRDC)
- **Key thresholds**: T_max forecasted to exceed 41°C triggers HAP
- **2010 heat wave**: 1,344 additional deaths in Ahmedabad
- **2015 validation**: <20 heat-related deaths in Ahmedabad vs 2,300+ across India
- **Vulnerable populations identified**: Elderly, outdoor workers, slum communities, children
- **Outdoor worker statistics**: 10% hospitalized at least once during summer, 50% wear thick cotton clothing
- **HAP strategies**: 1) Public awareness, 2) Early warning system (7-day forecast), 3) Healthcare worker training
- **Provenance**: REAL — published government/academic research

#### Source 3: NCDC Heat Surveillance Reports
- **NCDC**: National Centre for Disease Control, India
- **Role**: Heat-related illness and mortality surveillance data
- **Cited in**: Ahmedabad HAP evaluation studies
- **Provenance**: REAL — government health surveillance data

### Data Provenance — All Three Formats

#### Slide Content (for presentation)
- Left column: "Real Data" — ward shapes (OSM/MCGM), elderly % (Census 2011), risk coefficients (Gasparrini/Ahmedabad HAP), weather forecasts (Open-Meteo)
- Right column: "Modeled/Simulated" — risk scores, forecast values, alert dispatch, heat index/WBGT at ward centroids
- Label: "This is a hackathon prototype, not a production system"

#### README Section (project documentation)
- See "Data Sources" above for complete real data listing
- See "What's Modeled" below for simulation details
- All code references and documentation files link to sources

#### Database Comments (in SQL/PostGIS)
- Ward polygons: `source: 'OSM/MCGM'`
- Demographics: `source: 'Census 2011'`
- Weather data: `source: 'Open-Meteo API'`
- Risk coefficients: `source: 'Gasparrini et al. 2015 Lancet; Ahmedabad HAP 2013'`
- Risk scores: `note: 'modeled — not real mortality data'`
- Alerts: `note: 'sandbox demo — not production dispatch'`

### What's Real
- ✅ MCGM ward boundaries (public GIS data — when MCGM unavailable, OSM fallback)
- ✅ Census 2011 demographic data (public domain — ward-level CSV at data.opencity.in)
- ✅ Open-Meteo weather data (free, real-time model output)
- ✅ Published epidemiological coefficients (peer-reviewed: Gasparrini et al. 2015, Ahmedabad HAP 2013)
- ✅ Temperature-mortality relationships (Gasparrini et al. 2015: 384 locations, 13 countries)
- ✅ Ahmedabad HAP thresholds (41°C trigger, validated in 2015 evaluation)

### What's Modeled/Simulated
- 📊 Actual mortality numbers for Mumbai wards (not publicly granular — ward-level Mumbai mortality data unavailable)
- 📊 Real-time weather forecasts (Open-Meteo model outputs — probabilistic, not certain)
- 📊 Exact heat index/WBGT values at ward centroid (approximated from nearest grid point)
- 📊 Risk scores (modeled using Ahmedabad HAP coefficients applied to Mumbai context)
- 📊 Twilio/WhatsApp sandbox sends (test mode, not production)
- 📊 Risk score calculations (formula: base_risk × demographic_multiplier, capped at 100)

## Data Provenance — Detailed Breakdown

### Ward-Level Demographics (5 Demo Wards: 1-5)
- **Source**: Census 2011 Primary Census Abstract (data.opencity.in)
- **Fields**: Total Population, Males, Females, SC/ST Population, Ward Name
- **Age breakdown**: Elderly % (60+) estimated at 8.57% India-wide, ward-specific breakdown requires additional Census tables (HL-14 available at censusindia.gov.in)
- **Outdoor worker density**: Proxy based on economic survey + Census occupation tables
- **Real/Modeled**: REAL (demographics) — MODELED (age-specific breakdown by ward)

### Thermal Stress Indices (HI + WBGT)
- **Source**: pythermalcomfort library (v3.8.0)
- **Heat Index**: Lu & Romps (2022) — preferred over Rothfusz for extreme conditions
- **Wet Bulb Temperature**: wet_bulb_tmp from pythermalcomfort
- **WBGT**: Liljegren et al. (2008) with solar load via pythermalcomfort
- **Inputs**: Open-Meteo hourly temperature + relative humidity + wind speed + solar radiation
- **Real/Modeled**: REAL (equations and inputs) — MODELED (ward-level point estimates, not spatially interpolated)
- **Status**: ✅ Working in `ml/thermal_engine.py`

### ML Anomaly Detection
- **Model**: Isolation Forest (scikit-learn, pre-trained)
- **Training Data**: `data/mumbai_weather_real.csv` (17,545 real Mumbai weather records, 2024)
- **Features**: Temperature, humidity, wind_speed, solar_radiation
- **Purpose**: Detect unusual weather patterns beyond thermal indices
- **Status**: ✅ Pre-trained model at `ml/models/isolation_forest.joblib`

### Risk Scoring Formula
- **Source**: Ahmedabad Heat Action Plan (2013) + Gasparrini et al. (2015 Lancet)
- **Base risk**: From published temperature-mortality curves
- **Demographic multiplier**: Elderly % (Census 2011) + outdoor worker density (economic survey)
- **Thresholds**: 41°C T_max (Ahmedabad HAP validated trigger)
- **Real/Modeled**: REAL (published coefficients) — MODELED (applied to Mumbai context where Mumbai-specific coefficients unavailable)

### Alert Dispatch (SMS/WhatsApp)
- **Source**: Twilio Console + WhatsApp Cloud API (sandbox mode)
- **Test numbers**: +15551234567 (demo)
- **Real/Modeled**: SANDBOXED — test sends only, not production dispatch

## Role Responsibilities

| Role | Focus | Key Deliverable |
|------|-------|-----------------|
| R1 | Thermal Stress Engine | HI/WBGT via pythermalcomfort v3.8.0 (Lu & Romps 2022), Isolation Forest anomaly detection |
| R2 | Mortality Risk Model | Epidemiological risk scoring using Gasparrini/Ahmedabad HAP coefficients |
| R3 | Backend Engineer | FastAPI, PostGIS schema, Celery scheduled jobs |
| R4 | Frontend Engineer | React/Leaflet dashboard |
| R5 | Integration Engineer | ML→backend→frontend pipeline, Twilio/WA sandbox |
| R6 | Domain/Research Lead | Data sourcing, pitch deck, provenance documentation |

## Quick Start (Localhost)

```bash
# 1. Start services
brew services start postgresql@16  # or postgresql@17
brew services start redis

# 2. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with credentials
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Frontend
cd frontend
npm install
npm run dev -- --host 0.0.0.0

# 4. Seed data
cd scripts
python seed_wards.py
python ingest_weather.py
```

## Railway Deployment

Deploy the full stack on Railway (free tier, $5/month credit).

### Steps

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Init project
railway init

# 4. Add services
railway add postgresql
railway add redis

# 5. Set environment variables
railway variables set DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgresql:5432/heatwave"
railway variables set REDIS_URL="redis://redis:6379/0"
railway variables set ENVIRONMENT="production"

# 6. Deploy
railway up --build

# 7. Deploy worker and beat
railway up --build --service worker
railway up --build --service beat
```

### Railway Configuration
- **`railway.toml`**: Service definitions for postgresql and redis
- **`Procfile`**: Process types (web, worker, beat)
- **`Dockerfile`**: Backend Docker image
- **`docker-compose.yml`**: Local development with all services
- **`Dockerfile`** (frontend): React frontend image

### Local Development with Docker Compose
```bash
docker-compose up --build
```

### Environment Variables Required
- `DATABASE_URL`: PostgreSQL + asyncpg connection string
- `REDIS_URL`: Redis connection string for Celery broker
- `ENVIRONMENT`: development/production
- `FORECAST_REFRESH_HOURS`: How often to refresh forecasts (default: 6)
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_ACCESS_TOKEN`

## References

1. Gasparrini, A., Guo, Y., Hashizume, M., et al. (2015). "Mortality risk attributable to high and low ambient temperature: a multicountry observational study." The Lancet, 386(9991), 369-375. DOI: 10.1016/S0140-6736(14)62114-0

2. Mavalankar, D., et al. (2013). "Development and Implementation of South Asia's First Heat-Health Action Plan in Ahmedabad (Gujarat, India)." Indian Journal of Community Medicine, 38(Suppl 1), S9-S14.

3. Azhar, G.S., et al. (2014). "Heat-related mortality in India: a review of recent trends." International Journal of Environmental Research and Public Health, 11(11), 11378-11392.

4. National Disaster Management Authority (NDMA), Government of India. "Guidelines for Preparation of Action Plan – Prevention and Management of Heat Wave." 2016.

5. Tartarini, F., & Schiavon, S. (2020). "pythermalcomfort: A Python package for thermal comfort research." SoftwareX, 12, 100578.

6. Liljegren, J.I., et al. (2008). "A heat stress index for environmental monitoring." International Journal of Biometeorology, 53(3), 275-285.

7. Lu, Z., & Romps, D.M. (2022). "Heat Index: A Better Calculation." (Lu & Romps formulation used in pythermalcomfort)

8. Natural Resources Defense Council (NRDC). "Ahmedabad Heat Action Plan: Guide to Extreme Heat Planning in Ahmedabad, India." 2013. Available at: https://www.nrdc.org/sites/default/files/ahmedabad-heat-action-plan-2016.pdf

9. Census of India 2011. "Mumbai - Ward wise Census Data." Office of the Registrar General & Census Commissioner, India. Available at: https://data.opencity.in/dataset/mumbai-ward-wise-census-data

10. Open-Meteo API. "Weather Forecast API." https://open-meteo.com/api

## Data Sources — Complete URL List

| Data | Source | URL | Status |
|------|--------|-----|--------|
| Weather forecast | Open-Meteo API | https://open-meteo.com/api | ✅ Verified |
| Historical weather | Open-Meteo Archive API | https://archive-api.open-meteo.com | ✅ 17,545 records downloaded |
| Ward boundaries | OpenStreetMap Overpass | https://overpass-api.de/api/interpreter | ⚠️ 406 error — use MCGM |
| Ward census data | data.opencity.in | https://data.opencity.in/dataset/mumbai-ward-wise-census-data | ✅ Available |
| Elderly population | Census India | https://censusindia.gov.in | ✅ Available |
| Epidemiological coefficients | Gasparrini et al. 2015 | https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(14)62114-0/fulltext | ✅ Published |
| Ahmedabad HAP | NRDC/IIPH | https://www.nrdc.org/sites/default/files/ahmedabad-heat-action-plan-2016.pdf | ✅ Published |
| Heat vulnerability studies | PMC/NCBI | https://pmc.ncbi.nlm.nih.gov/articles/PMC4024996 | ✅ Published |
| Mumbai city data | census2011.co.in | https://www.census2011.co.in/census/district/357-mumbai-city.html | ✅ Available |
| MCGM open data | MCGM official | https://portal.mcgm.gov.in | ⚠️ To verify |
| Isolation Forest model | Trained locally | ml/models/isolation_forest.joblib | ✅ 2.8MB pre-trained |
| Real weather dataset | Open-Meteo Archive | data/mumbai_weather_real.csv | ✅ 17,545 records |
