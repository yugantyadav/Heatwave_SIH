from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models import Alert, Ward
from app.schemas import AlertTriggerRequest, AlertResponse, AlertLogResponse

router = APIRouter()

VALID_CATEGORIES = {"LOW", "MODERATE", "HIGH", "SEVERE"}

@router.post("/trigger", response_model=AlertResponse)
async def trigger(request: AlertTriggerRequest, db: AsyncSession = Depends(get_db)):
    ward_code = request.ward_code.strip()
    category = request.risk_category.strip().upper()
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown risk category: {request.risk_category}")
    ward = (await db.execute(select(Ward).where(Ward.ward_code == ward_code))).scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward not found: {ward_code}")
    external_id = f"demo_{ward_code}_{category}"
    # Idempotent: a repeat trigger for the same ward+category returns the
    # existing alert instead of stacking duplicates in the log.
    existing = (await db.execute(
        select(Alert).where(Alert.external_id == external_id).order_by(Alert.id.desc())
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