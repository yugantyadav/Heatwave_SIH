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
            async with session.get(cls.BASE_URL, params=params,
                                   timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                return await resp.json()

    @classmethod
    async def get_current_weather(cls, latitude: float, longitude: float):
        data = await cls.get_forecast(latitude, longitude, forecast_days=1)
        return data


def daily_heat_index_from_hourly(hourly: dict) -> list:
    """Build a 5-day outlook from HOURLY temp+humidity pairs.

    Each hour's Heat Index is computed from that same hour's temperature
    and humidity (Lu & Romps via ThermalIndexService), then grouped by
    day taking the daily max. Pairing each day's TMAX with the current
    humidity instead would inflate HI (e.g. afternoon heat + monsoon
    night humidity) — this was the pre-fix bug.
    """
    from app.services.thermal_index import ThermalIndexService

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rhs = hourly.get("relative_humidity_2m", [])

    by_day: dict = {}
    for i, ts in enumerate(times):
        try:
            t = float(temps[i])
            rh = float(rhs[i])
        except (IndexError, TypeError, ValueError):
            continue
        th = ThermalIndexService.calculate(t, rh)
        day = str(ts)[:10]
        slot = by_day.setdefault(day, {"date": day, "tmax": t, "heat_index": 0, "wbgt": 0})
        slot["tmax"] = max(slot["tmax"], t)
        hi = th.get("heat_index") or 0
        if hi > slot["heat_index"]:
            slot["heat_index"] = hi
            slot["wbgt"] = th.get("wbgt")
    return sorted(by_day.values(), key=lambda d: d["date"])[:5]


def daily_heat_index_forecast(forecast_path: str) -> list:
    import json

    with open(forecast_path) as f:
        fc = json.load(f)
    return daily_heat_index_from_hourly(fc.get("hourly", {}))


def forecast_file_is_fresh(forecast_path: str, horizon_days: int = 5) -> bool:
    """True when the bundled forecast still covers a full outlook from today.

    Testing only the LAST hourly slot is not enough: the file spans several
    days, so a file generated days ago keeps a future last slot and would
    report "fresh" long after its earliest days lapsed — the chart would then
    quietly render a truncated outlook instead of going live. Require the
    file to start no later than today *and* still reach the full horizon.
    """
    import json
    from datetime import date, timedelta

    try:
        with open(forecast_path) as f:
            fc = json.load(f)
        days = sorted({str(ts)[:10] for ts in fc.get("hourly", {}).get("time", []) if ts})
        if not days:
            return False
        today = date.today().isoformat()
        if days[0] > today:
            return False  # forecast starts in the future — nothing for today
        needed_last = (date.today() + timedelta(days=horizon_days - 1)).isoformat()
        return days[-1] >= needed_last
    except Exception:
        return False