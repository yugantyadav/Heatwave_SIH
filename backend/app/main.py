from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.session import engine, Base
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Heatwave EWS", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import wards_router, risk_router, weather_router, alerts_router, config_router
app.include_router(wards_router, prefix="/api/wards", tags=["wards"])
app.include_router(risk_router, prefix="/api/risk", tags=["risk"])
app.include_router(weather_router, prefix="/api/weather", tags=["weather"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(config_router, prefix="/api/config", tags=["config"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "heatwave-ews"}