from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import RiskScore
from app.schemas import RiskScoreResponse, RiskMapResponse
from sqlalchemy import select, desc

router = APIRouter()

@router.get("/wards", response_model=RiskMapResponse)
async def get_all_risks(db: AsyncSession = Depends(get_db)):
    # Latest score per ward (history table keeps every computation).
    result = await db.execute(select(RiskScore).order_by(desc(RiskScore.created_at)))
    latest = {}
    for r in result.scalars().all():
        latest.setdefault(r.ward_code, r)
    risks = sorted(latest.values(), key=lambda r: r.ward_code)
    return RiskMapResponse(wards=[RiskScoreResponse.model_validate(r) for r in risks])

@router.get("/wards/{ward_code}", response_model=RiskScoreResponse)
async def get_ward_risk(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskScore).where(RiskScore.ward_code == ward_code).order_by(desc(RiskScore.created_at)).limit(1))
    risk = result.scalar_one_or_none()
    if not risk:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Risk score not found")
    return RiskScoreResponse.model_validate(risk)