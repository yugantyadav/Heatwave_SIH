from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.db.session import get_db
from app.models import Ward, RiskScore, WeatherReading, Alert, ThresholdConfig, AdvisoryTemplate
from app.schemas import WardResponse, WardListResponse, WardGeoJSONResponse, RiskScoreResponse, RiskMapResponse, WeatherReadingResponse, WeatherForecastResponse, AlertTriggerRequest, AlertResponse, AlertLogResponse, ThresholdConfigResponse, AdvisoryTemplateResponse, HealthResponse
from typing import List, Optional, Dict, Any

router = APIRouter()

@router.get("/", response_model=WardListResponse)
async def get_wards(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ward).order_by(Ward.ward_code))
    wards = result.scalars().all()
    return WardListResponse(wards=wards)

@router.get("/geojson", response_model=WardGeoJSONResponse)
async def get_wards_geojson(db: AsyncSession = Depends(get_db)):
    """Serve real ward polygons from data/wards_geojson.json (generated from
    the Census CSV) enriched with live riskCategory from the latest RiskScore.
    Falls back to DB-only properties when the file is missing."""
    import json
    import os

    result = await db.execute(select(Ward))
    wards = result.scalars().all()
    risk_result = await db.execute(select(RiskScore).order_by(desc(RiskScore.created_at)))
    latest_by_ward = {}
    for r in risk_result.scalars().all():
        latest_by_ward.setdefault(r.ward_code, r.risk_category)

    geo_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "wards_geojson.json")
    geom_by_code = {}
    try:
        with open(os.path.normpath(geo_path)) as f:
            fc = json.load(f)
        for feat in fc.get("features", []):
            code = str(feat.get("properties", {}).get("ward_code"))
            geom_by_code[code] = feat.get("geometry")
    except Exception:
        geom_by_code = {}

    features = []
    for ward in wards:
        features.append({
            "type": "Feature",
            "properties": {
                "id": ward.ward_code,
                "ward_id": ward.id,
                "ward_code": ward.ward_code,
                "ward_name": ward.ward_name,
                "name": ward.ward_name,
                "zone": ward.zone,
                "district": ward.district,
                "total_population": ward.total_population,
                "elderly_percent": ward.elderly_percent,
                "riskCategory": (latest_by_ward.get(ward.ward_code) or "MODERATE"),
            },
            "geometry": geom_by_code.get(str(ward.ward_code)),
        })
    return WardGeoJSONResponse(type="FeatureCollection", features=features)

@router.get("/{ward_code}", response_model=WardResponse)
async def get_ward(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ward).where(Ward.ward_code == ward_code))
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return WardResponse.model_validate(ward)

@router.get("/risk/wards", response_model=RiskMapResponse)
async def get_ward_risks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskScore).order_by(desc(RiskScore.created_at)))
    latest = {}
    for r in result.scalars().all():
        latest.setdefault(r.ward_code, r)
    risks = sorted(latest.values(), key=lambda r: r.ward_code)
    return RiskMapResponse(wards=[RiskScoreResponse.model_validate(r) for r in risks])

@router.get("/risk/wards/{ward_code}", response_model=RiskScoreResponse)
async def get_ward_risk(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskScore).where(RiskScore.ward_code == ward_code).order_by(desc(RiskScore.created_at)).limit(1))
    risk = result.scalar_one_or_none()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk score not found")
    return RiskScoreResponse.model_validate(risk)

@router.get("/weather/wards/{ward_code}/current", response_model=WeatherReadingResponse)
async def get_current_weather(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherReading).where(WeatherReading.ward_code == ward_code).order_by(desc(WeatherReading.recorded_at)).limit(1)
    )
    reading = result.scalar_one_or_none()
    if not reading:
        raise HTTPException(status_code=404, detail="Weather reading not found")
    return WeatherReadingResponse.model_validate(reading)

@router.get("/weather/wards/{ward_code}/forecast", response_model=WeatherForecastResponse)
async def get_forecast(ward_code: str, db: AsyncSession = Depends(get_db)):
    import json
    import os

    from app.services.thermal_index import ThermalIndexService

    result = await db.execute(
        select(WeatherReading).where(WeatherReading.ward_code == ward_code).order_by(desc(WeatherReading.recorded_at))
    )
    readings = result.scalars().all()
    current = readings[0] if readings else None

    forecast = []
    try:
        fc_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mumbai_weather_forecast.json"))
        with open(fc_path) as f:
            fc = json.load(f)
        daily = fc.get("daily", {})
        times = daily.get("time", [])
        tmax = daily.get("temperature_2m_max", [])
        rh = (current.relative_humidity_2m if current and current.relative_humidity_2m else 80.0)
        for i, d in enumerate(times):
            t = float(tmax[i])
            th = ThermalIndexService.calculate(t, rh)
            forecast.append({
                "date": d,
                "tmax": t,
                "heat_index": th.get("heat_index"),
                "wbgt": th.get("wbgt"),
            })
    except Exception:
        forecast = []
    return WeatherForecastResponse(
        ward_code=ward_code,
        current=WeatherReadingResponse.model_validate(current) if current else None,
        forecast=forecast
    )

@router.post("/alerts/trigger", response_model=AlertResponse)
async def trigger_alert(request: AlertTriggerRequest, db: AsyncSession = Depends(get_db)):
    alert = Alert(
        ward_code=request.ward_code,
        alert_channel=request.channel,
        message=request.message,
        triggered_by=request.risk_category,
        alert_status="pending",
        external_id=f"demo_{request.ward_code}_{request.risk_category}"
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)

@router.get("/alerts/", response_model=AlertLogResponse)
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).order_by(desc(Alert.sent_at)))
    alerts = result.scalars().all()
    return AlertLogResponse(alerts=[AlertResponse.model_validate(a) for a in alerts])

@router.get("/config/thresholds", response_model=List[ThresholdConfigResponse])
async def get_thresholds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ThresholdConfig))
    configs = result.scalars().all()
    return [ThresholdConfigResponse.model_validate(c) for c in configs]

@router.get("/config/advisories", response_model=List[AdvisoryTemplateResponse])
async def get_advisories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdvisoryTemplate))
    templates = result.scalars().all()
    return [AdvisoryTemplateResponse.model_validate(t) for t in templates]

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", service="heatwave-ews")