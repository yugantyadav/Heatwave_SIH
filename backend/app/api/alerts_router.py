from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models import Alert
from app.schemas import AlertTriggerRequest, AlertResponse, AlertLogResponse

router = APIRouter()

@router.post("/trigger", response_model=AlertResponse)
async def trigger(request: AlertTriggerRequest, db: AsyncSession = Depends(get_db)):
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

@router.get("/", response_model=AlertLogResponse)
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).order_by(desc(Alert.sent_at)))
    alerts = result.scalars().all()
    return AlertLogResponse(alerts=[AlertResponse.model_validate(a) for a in alerts])