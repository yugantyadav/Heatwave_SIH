"""initial heatwave schema

Revision ID: e8d1501abdf9
Revises: 
Create Date: 2026-09-21 20:41:22.032175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8d1501abdf9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Baseline revision: application tables (wards, weather_readings,
    risk_scores, alerts, threshold_configs, advisory_templates) are
    created by app startup (Base.metadata.create_all) and seeded by
    scripts/seed_wards.py + scripts/ingest_weather.py. PostGIS system
    tables (spatial_ref_sys, geography_columns, geometry_columns) are
    intentionally excluded — see include_object in alembic/env.py.
    """
    pass


def downgrade() -> None:
    """Downgrade schema (baseline: no-op)."""
    pass
