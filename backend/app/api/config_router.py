from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Dict, List, Union
from app.db.session import get_db
from app.models import ThresholdConfig, AdvisoryTemplate
from app.schemas import ThresholdConfigResponse, AdvisoryTemplateResponse

router = APIRouter()

@router.get("/thresholds", response_model=list[ThresholdConfigResponse])
async def get_thresholds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ThresholdConfig))
    configs = result.scalars().all()
    return [ThresholdConfigResponse.model_validate(c) for c in configs]

@router.post("/thresholds", response_model=list[ThresholdConfigResponse])
async def save_thresholds(payload: Union[List[Dict[str, Any]], Dict[str, Any]], db: AsyncSession = Depends(get_db)):
    """Accept the frontend object shape {Low:{maxHeatIndexC,maxWbgtC},...}
    or a raw list of ThresholdConfig rows; upsert and return all rows."""
    rows: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        hi = {"config_type": "heat_index"}
        wb = {"config_type": "wbgt"}
        for cat in ("Low", "Moderate", "High", "Severe"):
            node = payload.get(cat, {}) or {}
            hi[cat.lower() + "_threshold"] = node.get("maxHeatIndexC")
            wb[cat.lower() + "_threshold"] = node.get("maxWbgtC")
        rows = [hi, wb]
    else:
        rows = payload
    for r in rows:
        ctype = r.get("config_type")
        if not ctype:
            continue
        result = await db.execute(select(ThresholdConfig).where(ThresholdConfig.config_type == ctype))
        existing = result.scalar_one_or_none()
        keys = ("low_threshold", "moderate_threshold", "high_threshold", "severe_threshold")
        if existing:
            # Keys present with an explicit null clear the value (blank Severe
            # = "no upper bound"); absent keys are left untouched.
            for k in keys:
                if k in r:
                    setattr(existing, k, r.get(k))
        else:
            db.add(ThresholdConfig(config_type=ctype, **{k: r.get(k) for k in keys if k in r}))
    await db.commit()
    result = await db.execute(select(ThresholdConfig))
    return [ThresholdConfigResponse.model_validate(c) for c in result.scalars().all()]

@router.get("/advisories", response_model=list[AdvisoryTemplateResponse])
async def get_advisories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdvisoryTemplate))
    templates = result.scalars().all()
    return [AdvisoryTemplateResponse.model_validate(t) for t in templates]

@router.post("/advisories", response_model=list[AdvisoryTemplateResponse])
async def save_advisories(payload: Union[List[Dict[str, Any]], Dict[str, Any]], db: AsyncSession = Depends(get_db)):
    """Accept {Low:'text',...} or a list of AdvisoryTemplate rows; upsert.
    Unknown risk categories are ignored so stray payloads can't pollute
    the table."""
    valid = {"LOW", "MODERATE", "HIGH", "SEVERE"}
    rows: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        for cat, text in payload.items():
            key = str(cat).upper()
            if key not in valid:
                continue
            if isinstance(text, str):
                rows.append({"risk_category": key, "sms_text": text, "whatsapp_text": text})
            elif isinstance(text, dict):
                rows.append({
                    "risk_category": key,
                    "sms_text": text.get("sms_text", ""),
                    "whatsapp_text": text.get("whatsapp_text", text.get("sms_text", "")),
                })
    else:
        for r in payload:
            if str(r.get("risk_category", "")).upper() in valid:
                rows = rows + [r]
        rows = rows
    for r in rows:
        cat = str(r.get("risk_category", "")).upper()
        if not cat:
            continue
        result = await db.execute(select(AdvisoryTemplate).where(AdvisoryTemplate.risk_category == cat))
        existing = result.scalar_one_or_none()
        if existing:
            existing.sms_text = r.get("sms_text", existing.sms_text)
            existing.whatsapp_text = r.get("whatsapp_text", existing.whatsapp_text)
        else:
            db.add(AdvisoryTemplate(risk_category=cat, sms_text=r.get("sms_text", ""), whatsapp_text=r.get("whatsapp_text", "")))
    await db.commit()
    result = await db.execute(select(AdvisoryTemplate))
    return [AdvisoryTemplateResponse.model_validate(t) for t in result.scalars().all()]