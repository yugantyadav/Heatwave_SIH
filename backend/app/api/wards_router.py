from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.queries import latest_risk_per_ward
from app.db.session import get_db
from app.models import Ward
from app.schemas import WardResponse, WardListResponse, WardGeoJSONResponse, HealthResponse

router = APIRouter()

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
    import os

    result = await db.execute(select(Ward))
    wards = result.scalars().all()
    risk_result = await db.execute(latest_risk_per_ward())
    latest_by_ward = {r.ward_code: r.risk_category for r in risk_result.scalars().all()}

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
