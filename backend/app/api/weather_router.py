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
        select(WeatherReading).where(WeatherReading.ward_code == ward_code).order_by(desc(WeatherReading.recorded_at)).limit(1)
    )
    reading = result.scalar_one_or_none()
    if not reading:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Weather reading not found")
    return WeatherReadingResponse.model_validate(reading)

@router.get("/wards/{ward_code}/forecast", response_model=WeatherForecastResponse)
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