# Documentation

Project documentation for the Heatwave Early Warning System hackathon submission.

## Project Overview

- **Problem Statement**: 26083
- **Timeline**: 14 days (2 weeks)
- **Demo city**: Mumbai (MCGM ward boundaries)
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

Day-by-day roadmap for team members to follow. Each role takes specific days for their component, with integration points marked.

## Judge Q&A Readiness

Approved answers for common judge questions about accuracy, sandbox capability, and methodology choices.

## Data Sources

- Open-Meteo weather API
- MCGM ward boundaries (OSM/Overpass)
- Census 2011 demographic data
- Ahmedabad Heat Action Plan studies (for risk coefficients)

## Data Provenance

What's real vs. what's modeled/simulated, clearly labeled for judges.

## Role Responsibilities

| Role | Focus | Key Deliverable |
|------|-------|-----------------|
| R1 | Thermal Stress Engine | HI + WBGT calculations |
| R2 | Mortality Risk Model | Epidemiological risk scoring |
| R3 | Backend Engineer | FastAPI, PostGIS, Celery |
| R4 | Frontend Engineer | React/Leaflet dashboard |
| R5 | Integration Engineer | ML→backend→frontend pipeline |
| R6 | Domain/Research Lead | Data sourcing, pitch deck |

## Quick Start

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```