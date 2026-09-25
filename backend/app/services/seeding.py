"""Idempotent database seeding.

Why this exists: the app is deployed to a *fresh* Render Postgres where
``Base.metadata.create_all`` builds the tables but leaves them empty. That
produced a dashboard where every endpoint returned 200 and the map rendered
zero wards — a healthy-looking service showing nothing. It also happens
whenever the free Postgres expires and is recreated.

``ensure_seeded`` runs at the top of the pipeline and fills in anything
missing, so a cold deploy is self-healing. It only ever inserts what is
absent: existing wards, thresholds and advisories are never overwritten, so
admin edits survive restarts and redeploys.
"""
import csv
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdvisoryTemplate, ThresholdConfig, Ward

# backend/app/services -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
CENSUS_CSV = DATA_DIR / "mumbai_ward_census.csv"
AREAS_GEOJSON = DATA_DIR / "wards_geojson.json"

# Defaults match what the Admin Panel shipped with. Severe is blank (NULL) on
# purpose: it means "no upper bound", and the editor rejects 0.
DEFAULT_THRESHOLDS = [
    {"config_type": "heat_index", "low_threshold": 29, "moderate_threshold": 38,
     "high_threshold": 47, "severe_threshold": None},
    {"config_type": "wbgt", "low_threshold": 27, "moderate_threshold": 30,
     "high_threshold": 39, "severe_threshold": None},
]

DEFAULT_ADVISORIES = {
    "LOW": "Routine conditions. No special precautions needed.",
    "MODERATE": "Sensitive groups (elderly, young children, outdoor workers) should limit prolonged sun exposure between 12 PM and 4 PM.",
    "HIGH": "Outdoor work should be rescheduled outside peak hours. Ensure hydration stations are active at outdoor worksites.",
    "SEVERE": "Dangerous conditions. Avoid all non-essential outdoor exposure. Activate ward-level heat action plan and cooling shelters.",
}


def _ward_from_census(row: dict) -> dict:
    code = row["Ward Code"].strip()
    name = row["Ward Name"].strip()
    return {
        "ward_code": code,
        "ward_name": f"Ward {code} ({name})",
        "zone": name,
        "district": row["District Name"].strip(),
        "total_population": int(row["Total Population"] or 0),
        "total_males": int(row["Total Males"] or 0),
        "total_females": int(row["Total Females"] or 0),
        "sc_population": int(row["SC Population"] or 0),
        "st_population": int(row["ST Population"] or 0),
        # Prototype defaults (documented, not census-measured):
        "elderly_percent": 8.57,
        "outdoor_worker_density": 0.5,
    }


def _ward_from_area(feat: dict) -> dict:
    p = feat.get("properties", {})
    # A census cell of 0.0 is a real value, not a missing one.
    elderly = p.get("elderly_percent")
    return {
        "ward_code": str(p["ward_code"]),
        "ward_name": p["ward_name"],
        "zone": p.get("zone"),
        "district": p.get("district"),
        "geometry": json.dumps(feat.get("geometry")),
        "total_population": int(p.get("total_population") or 0),
        "total_males": 0,
        "total_females": 0,
        "sc_population": 0,
        "st_population": 0,
        "elderly_percent": float(elderly) if elderly not in (None, "") else 8.57,
        "outdoor_worker_density": 0.5,
    }


def load_ward_rows() -> list[dict]:
    """Census demographics + the polygon-backed map wards."""
    rows: list[dict] = []
    if CENSUS_CSV.exists():
        with open(CENSUS_CSV, newline="") as f:
            rows.extend(_ward_from_census(r) for r in csv.DictReader(f))
    if AREAS_GEOJSON.exists():
        with open(AREAS_GEOJSON) as f:
            for feat in json.load(f).get("features", []):
                rows.append(_ward_from_area(feat))
    return rows


async def ensure_seeded(session: AsyncSession) -> dict:
    """Insert anything missing. Never overwrites existing rows."""
    result = {"wards": 0, "thresholds": 0, "advisories": 0, "skipped": False}

    ward_count = (await session.execute(select(func.count()).select_from(Ward))).scalar_one()
    if ward_count == 0:
        rows = load_ward_rows()
        for row in rows:
            existing = (await session.execute(
                select(Ward).where(Ward.ward_code == row["ward_code"])
            )).scalar_one_or_none()
            if existing is None:
                session.add(Ward(**row))
                result["wards"] += 1
    else:
        result["skipped"] = True

    thr_count = (await session.execute(select(func.count()).select_from(ThresholdConfig))).scalar_one()
    if thr_count == 0:
        for row in DEFAULT_THRESHOLDS:
            session.add(ThresholdConfig(**row))
            result["thresholds"] += 1

    adv_count = (await session.execute(select(func.count()).select_from(AdvisoryTemplate))).scalar_one()
    if adv_count == 0:
        for category, text in DEFAULT_ADVISORIES.items():
            session.add(AdvisoryTemplate(risk_category=category, sms_text=text, whatsapp_text=text))
            result["advisories"] += 1

    await session.commit()
    return result


def data_files_present() -> bool:
    """False in a container built without data/ — seeding would be a no-op."""
    return CENSUS_CSV.exists() or AREAS_GEOJSON.exists()


def describe_paths() -> str:
    return f"census={CENSUS_CSV.exists()} areas={AREAS_GEOJSON.exists()} dir={DATA_DIR}"
