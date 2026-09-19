from fastapi import APIRouter
from app.api.wards_router import router as wards_router
from app.api.risk_router import router as risk_router
from app.api.weather_router import router as weather_router
from app.api.alerts_router import router as alerts_router
from app.api.config_router import router as config_router

app = APIRouter()
app.include_router(wards_router)
app.include_router(risk_router)
app.include_router(weather_router)
app.include_router(alerts_router)
app.include_router(config_router)