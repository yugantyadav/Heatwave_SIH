from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import create_engine, text
from app.db.session import Base
from app.core.config import settings

_sync_engine = create_engine(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "sqlite:///"), echo=False)

async def _refresh_weather_on_startup():
    """Best-effort weather + forecast-file refresh when the API boots, so a
    cold start never serves a stale bundled forecast."""
    try:
        from app.tasks.weather_tasks import _refresh_async
        await _refresh_async()
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=_sync_engine)
    # Belt-and-braces dedup: app-level checks guard triggers, this index
    # stops racing writers from stacking duplicates. Best-effort — an
    # existing dup would only warn, never block startup.
    try:
        with _sync_engine.begin() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_alerts_external_id "
                "ON alerts (external_id)"
            ))
    except Exception:
        pass
    refresh_task = None
    if settings.ENVIRONMENT != "test":
        refresh_task = asyncio.create_task(_refresh_weather_on_startup())
    yield
    if refresh_task:
        refresh_task.cancel()
    _sync_engine.dispose()

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

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "heatwave-ews"}
