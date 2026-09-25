from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models import WeatherReading
from app.schemas import WeatherReadingResponse, WeatherForecastResponse
from app.services.weather import daily_heat_index_forecast, daily_heat_index_from_hourly, forecast_file_is_fresh

router = APIRouter()

MUMBAI_LAT, MUMBAI_LON = 19.076, 72.8777

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


def _forecast_file_path() -> str:
    import os
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mumbai_weather_forecast.json"))


async def _live_forecast() -> list | None:
    """Fetch today's forecast straight from Open-Meteo; None on any failure."""
    from app.services.weather import WeatherService

    try:
        data = await WeatherService.get_forecast(MUMBAI_LAT, MUMBAI_LON, forecast_days=5)
        return daily_heat_index_from_hourly(data.get("hourly", {}))
    except Exception:
        return None


@router.get("/wards/{ward_code}/forecast", response_model=WeatherForecastResponse)
async def get_forecast(ward_code: str, db: AsyncSession = Depends(get_db)):
    from datetime import datetime

    result = await db.execute(
        select(WeatherReading).where(WeatherReading.ward_code == ward_code).order_by(desc(WeatherReading.recorded_at))
    )
    readings = result.scalars().all()
    current = readings[0] if readings else None

    fc_path = _forecast_file_path()
    forecast: list = []
    # Prefer a live fetch when the bundled file has aged out (it only
    # covers the days it was generated for); fall back to the file.
    if not forecast_file_is_fresh(fc_path):
        forecast = await _live_forecast() or []
    if not forecast:
        try:
            forecast = daily_heat_index_forecast(fc_path)
        except Exception:
            forecast = []
    # Never serve days that already passed.
    today = datetime.now().date().isoformat()
    forecast = [d for d in forecast if str(d.get("date", "")) >= today]
    return WeatherForecastResponse(
        ward_code=ward_code,
        current=WeatherReadingResponse.model_validate(current) if current else None,
        forecast=forecast
    )