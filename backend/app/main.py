from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import text
from app.db.session import Base, engine
from app.core.config import settings

# DDL is issued through the *async* engine via run_sync. The previous sync
# engine was built from DATABASE_URL, so under a postgresql+asyncpg URL it
# tried to run DDL on an async driver from sync code and died with
# MissingGreenlet before the app ever served a request.
def _create_schema(sync_conn):
    Base.metadata.create_all(bind=sync_conn)
    # Belt-and-braces dedup: app-level checks guard triggers, this index stops
    # racing writers from stacking duplicates. Best-effort — an existing dup
    # would only warn, never block startup.
    for ddl in (
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_alerts_external_id ON alerts (external_id)",
        "CREATE INDEX IF NOT EXISTS ix_risk_scores_ward_created ON risk_scores (ward_code, created_at)",
    ):
        try:
            sync_conn.execute(text(ddl))
        except Exception:
            pass

async def _bootstrap_pipeline():
    """Best-effort refresh -> compute -> trigger when the API boots.

    Celery's schedule is a delay, so a cold start used to leave the map with no
    risk scores (and therefore a blank/optimistic map) until the first period
    elapsed. Running the ordered pipeline here closes that gap."""
    try:
        from app.tasks.weather_tasks import _pipeline_async
        await _pipeline_async()
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(_create_schema)
    bootstrap = None
    if settings.ENVIRONMENT != "test":
        bootstrap = asyncio.create_task(_bootstrap_pipeline())
    yield
    if bootstrap:
        bootstrap.cancel()
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

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "heatwave-ews"}
