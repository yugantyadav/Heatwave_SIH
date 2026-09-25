"""Shared fixtures. DATABASE_URL is pointed at a throwaway SQLite file
BEFORE any app module is imported (settings/engine are module-level)."""
import os
import sys
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="heatwave-tests-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DIR}/test.db"
os.environ["ENVIRONMENT"] = "test"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, AsyncSessionLocal
from app.models import Ward, ThresholdConfig


def _seed():
    """Two wards + the default admin thresholds so API tests have data."""
    import asyncio

    async def run():
        async with AsyncSessionLocal() as session:
            session.add(Ward(ward_code="A", ward_name="Ward A", zone="Zone 1",
                             district="Mumbai", total_population=120000,
                             elderly_percent=8.57, outdoor_worker_density=0.5))
            session.add(Ward(ward_code="B", ward_name="Ward B", zone="Zone 2",
                             district="Mumbai", total_population=80000,
                             elderly_percent=9.1, outdoor_worker_density=0.4))
            session.add(ThresholdConfig(config_type="heat_index", low_threshold=29,
                                        moderate_threshold=38, high_threshold=47,
                                        severe_threshold=None))
            session.add(ThresholdConfig(config_type="wbgt", low_threshold=27,
                                        moderate_threshold=30, high_threshold=39,
                                        severe_threshold=58))
            await session.commit()

    asyncio.run(run())


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        _seed()
        yield c
