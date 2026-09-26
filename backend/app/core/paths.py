"""Filesystem layout for bundled data files.

The backend reaches for ``data/`` (ward polygons, Census CSV, forecast JSON)
and ``ml/`` relative to the source tree. That works locally, where the code
lives at ``Heatwave/backend/app/...`` and the data sits two levels up. It
breaks in the container, where the Dockerfile flattens ``backend/*`` into
``/app`` so the code lives at ``/app/app/...`` — one level shallower, and a
fixed ``../../..`` lands on ``/`` instead of the app root.

The failure was silent: seeding inserted zero wards and the geojson endpoint
returned an empty FeatureCollection, so the app looked healthy (200s) while
rendering a blank map. Resolving by *searching* for the data directory makes
both layouts work and keeps a single definition.
"""
import os
from pathlib import Path

# Files that must exist for the directory to be recognised as the data dir.
_DATA_MARKERS = ("wards_geojson.json", "mumbai_ward_census.csv")
_ML_MARKERS = ("models",)
FORECAST_FILENAME = "mumbai_weather_forecast.json"
GEOJSON_FILENAME = "wards_geojson.json"


def _find_upwards(start: Path, folder: str, markers: tuple[str, ...]) -> Path | None:
    """Walk up from ``start`` looking for ``folder`` that contains a marker."""
    for parent in start.resolve().parents:
        candidate = parent / folder
        for marker in markers:
            if (candidate / marker).exists():
                return candidate
    return None


def resolve_dir(start: Path, folder: str, markers: tuple[str, ...]) -> Path:
    """Locate ``folder`` by walking up, with a best-effort fallback.

    The fallback returns the conventional location even when the marker is
    missing, so a misconfigured deploy still reports a real path in logs
    rather than raising deep inside a request.
    """
    override = os.environ.get(f"HEATWAVE_{folder.upper()}_DIR")
    if override:
        return Path(override)
    found = _find_upwards(start, folder, markers)
    if found:
        return found
    # backend/app/x -> backend is one level up from the package
    return start.resolve().parents[2] / folder


def data_dir(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve().parent
    return resolve_dir(start, "data", _DATA_MARKERS)


def ml_dir(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve().parent
    return resolve_dir(start, "ml", _ML_MARKERS)


def forecast_path(start: Path | None = None) -> Path:
    return data_dir(start) / FORECAST_FILENAME


def geojson_path(start: Path | None = None) -> Path:
    return data_dir(start) / GEOJSON_FILENAME


def data_is_present(start: Path | None = None) -> bool:
    d = data_dir(start)
    return all((d / m).exists() for m in _DATA_MARKERS)
