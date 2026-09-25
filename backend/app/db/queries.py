"""Reusable SELECT statements.

``latest_risk_per_ward`` exists because "latest score per ward" was
implemented three separate times by loading the entire ``risk_scores`` table
into Python and keeping the first row per ward. That table is append-only
(+one row per ward per scheduled run), so the map endpoint was re-reading
the entire history on every dashboard load. The window function below does
the same reduction in the database.
"""
from sqlalchemy import func, select

from app.models import RiskScore


def latest_risk_per_ward():
    """SELECT of the newest RiskScore row for every ward.

    Orders by ``created_at`` with ``id`` as tie-breaker, so rows written in
    the same clock tick still resolve deterministically to the newest.
    """
    ranked = select(
        RiskScore.id.label("id"),
        func.row_number().over(
            partition_by=RiskScore.ward_code,
            order_by=(RiskScore.created_at.desc(), RiskScore.id.desc()),
        ).label("rn"),
    ).subquery()
    return (
        select(RiskScore)
        .join(ranked, RiskScore.id == ranked.c.id)
        .where(ranked.c.rn == 1)
    )
