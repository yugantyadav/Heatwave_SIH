from datetime import timedelta
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.core.config import settings
from app.core.paths import geojson_path
from app.db.queries import latest_risk_per_ward
from app.db.session import AsyncSessionLocal, get_db
from app.models import Ward, WeatherReading
from app.schemas import WardResponse, WardListResponse, WardGeoJSONResponse, HealthResponse
from app.services.alerting import utcnow

router = APIRouter()

# Staleness self-heal. On Render's free tier nothing runs on a schedule, so
# the read path notices stale data and kicks the pipeline. The flag keeps a
# burst of requests from starting several pipelines at once.
_refresh_lock = asyncio.Lock()
_refresh_in_flight = False


async def _newest_reading_at():
    async with AsyncSessionLocal() as s:
        return (await s.execute(select(func.max(WeatherReading.recorded_at)))).scalar_one()


async def _refresh_if_stale() -> None:
    """Start the pipeline in the background if the data is older than allowed.

    Never raises into the request and never blocks it: the cheap staleness
    check is one indexed MAX(), and the pipeline itself is detached.
    """
    global _refresh_in_flight
    if _refresh_in_flight:
        return
    try:
        newest = await _newest_reading_at()
        max_age = timedelta(minutes=max(int(settings.DATA_MAX_AGE_MINUTES), 1))
        if newest is not None and utcnow() - newest < max_age:
            return
    except Exception:
        return
    async with _refresh_lock:
        if _refresh_in_flight:
            return
        _refresh_in_flight = True
    asyncio.create_task(_run_pipeline())


async def _run_pipeline() -> None:
    global _refresh_in_flight
    try:
        from app.tasks.weather_tasks import _pipeline_async
        await _pipeline_async()
    except Exception:
        pass
    finally:
        _refresh_in_flight = False


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", service="heatwave-ews")

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

    # With no background worker there is nothing to refresh on a schedule, so
    # the first read after the data goes stale triggers the pipeline inline.
    # Cheap guard: one indexed MAX() query, and it only does network work when
    # the data is actually old.
    await _refresh_if_stale()

    result = await db.execute(select(Ward))
    wards = result.scalars().all()
    risk_result = await db.execute(latest_risk_per_ward())
    latest_by_ward = {r.ward_code: r.risk_category for r in risk_result.scalars().all()}

    geom_by_code = {}
    geo_path = geojson_path()
    try:
        with open(geo_path) as f:
            fc = json.load(f)
        for feat in fc.get("features", []):
            code = str(feat.get("properties", {}).get("ward_code"))
            geom_by_code[code] = feat.get("geometry")
    except Exception:
        geom_by_code = {}

    features = []
    for ward in wards:
        # Only wards with a mapped polygon are part of the map layer
        # (the 8 area-specific wards from data/wards_geojson.json).
        # Census-only wards stay in the DB for demographics but are not drawn.
        geometry = geom_by_code.get(str(ward.ward_code))
        if geometry is None:
            continue
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
            "geometry": geometry,
        })
    return WardGeoJSONResponse(type="FeatureCollection", features=features)

@router.get("/{ward_code}", response_model=WardResponse)
async def get_ward(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ward).where(Ward.ward_code == ward_code))
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return WardResponse.model_validate(ward)
