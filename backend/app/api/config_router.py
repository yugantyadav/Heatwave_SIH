from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models import ThresholdConfig, AdvisoryTemplate
from app.schemas import ThresholdConfigResponse, AdvisoryTemplateResponse

router = APIRouter()

@router.get("/thresholds", response_model=list[ThresholdConfigResponse])
async def get_thresholds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ThresholdConfig))
    configs = result.scalars().all()
    return [ThresholdConfigResponse.model_validate(c) for c in configs]

@router.get("/advisories", response_model=list[AdvisoryTemplateResponse])
async def get_advisories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdvisoryTemplate))
    templates = result.scalars().all()
    return [AdvisoryTemplateResponse.model_validate(t) for t in templates]