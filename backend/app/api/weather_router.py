from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models import WeatherReading
from app.schemas import WeatherReadingResponse, WeatherForecastResponse

router = APIRouter()

@router.get("/wards/{ward_code}/current", response_model=WeatherReadingResponse)
async def get_current(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherReading).where(WeatherReading.ward_code == ward_code).order_by(desc(WeatherReading.recorded_at))
    )
    reading = result.scalar_one_or_none()
    if not reading:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Weather reading not found")
    return WeatherReadingResponse.model_validate(reading)

@router.get("/wards/{ward_code}/forecast", response_model=WeatherForecastResponse)
async def get_forecast(ward_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherReading).where(WeatherReading.ward_code == ward_code).order_by(desc(WeatherReading.recorded_at))
    )
    readings = result.scalars().all()
    current = readings[0] if readings else None
    return WeatherForecastResponse(
        ward_code=ward_code,
        current=WeatherReadingResponse.model_validate(current) if current else None,
        forecast=[]
    )