from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.config import settings
from app.db.session import get_db
from app.models import Alert, Ward
from app.schemas import AlertTriggerRequest, AlertResponse, AlertLogResponse
from app.services.alerting import (
    DEFAULT_MANUAL_WINDOW_SECONDS,
    VALID_CATEGORIES,
    external_id_for,
    utcnow,
)

router = APIRouter()

@router.post("/trigger", response_model=AlertResponse)
async def trigger(request: AlertTriggerRequest, db: AsyncSession = Depends(get_db)):
    ward_code = request.ward_code.strip()
    category = request.risk_category.strip().upper()
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown risk category: {request.risk_category}")
    ward = (await db.execute(select(Ward).where(Ward.ward_code == ward_code))).scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward not found: {ward_code}")
    # Collapse only accidental double-sends inside a short window; a genuine
    # later re-alert gets its own row instead of replaying a stale one.
    window = int(settings.MANUAL_ALERT_WINDOW_SECONDS or DEFAULT_MANUAL_WINDOW_SECONDS)
    external_id = external_id_for("demo", ward_code, category, utcnow(), window)
    existing = (await db.execute(
        select(Alert).where(Alert.external_id == external_id)
    )).scalars().first()
    if existing:
        return AlertResponse.model_validate(existing)
    alert = Alert(
        ward_code=ward_code,
        alert_channel=request.channel,
        message=request.message,
        triggered_by=category,
        alert_status="pending",
        external_id=external_id,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)

@router.get("/", response_model=AlertLogResponse)
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).order_by(desc(Alert.sent_at)))
    alerts = result.scalars().all()
    return AlertLogResponse(alerts=[AlertResponse.model_validate(a) for a in alerts])