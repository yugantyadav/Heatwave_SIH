# Weather service
import aiohttp
from app.core.config import settings

class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @classmethod
    async def get_forecast(cls, latitude: float, longitude: float, forecast_days: int = 5):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,weathercode",
            "daily": "temperature_2m_max,temperature_2m_min,weathercode",
            "timezone": "Asia/Kolkata",
            "forecast_days": forecast_days,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(cls.BASE_URL, params=params) as resp:
                return await resp.json()

    @classmethod
    async def get_current_weather(cls, latitude: float, longitude: float):
        data = await cls.get_forecast(latitude, longitude, forecast_days=1)
        return data