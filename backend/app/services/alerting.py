"""Alert identity + de-duplication rules shared by the Celery task and the
manual trigger endpoint.

An alert is identified by ``(namespace, ward, category, time window)``. The
window is baked into ``external_id``, which is UNIQUE in the database, so
"at most one alert per ward+category per window" is enforced by the database
itself rather than by a scan-then-insert race.

Why a window at all: the previous scheme keyed alerts on
``(ward_code, triggered_by)`` with no time component, so a ward could only
ever emit one alert per category for the lifetime of the database — after
dropping to LOW and climbing back to HIGH days later it stayed silent, which
is the exact case an early-warning system must not miss.
"""
from datetime import datetime, timezone

# Categories that warrant a public alert (LOW/MODERATE stay informational).
ALERT_CATEGORIES = ("HIGH", "SEVERE")
# Every category the API accepts on a manual trigger.
VALID_CATEGORIES = ("LOW", "MODERATE", "HIGH", "SEVERE")

# Fallbacks used when no Settings value is supplied.
DEFAULT_COOLDOWN_HOURS = 6
DEFAULT_MANUAL_WINDOW_SECONDS = 300


def utcnow() -> datetime:
    """Naive UTC — matches the naive-UTC values stored by the ORM defaults."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def window_bucket(when: datetime, window_seconds: int) -> int:
    """Stable bucket index for ``when``. Buckets advance every
    ``window_seconds``; two calls in the same window share a bucket."""
    window = max(int(window_seconds or 1), 1)
    return int(when.replace(tzinfo=timezone.utc).timestamp()) // window


def external_id_for(namespace: str, ward_code: str, category: str, when: datetime,
                    window_seconds: int) -> str:
    return f"{namespace}_{ward_code}_{category}_{window_bucket(when, window_seconds)}"


def should_alert(last_alert_at: datetime | None, now: datetime, cooldown_hours: int) -> bool:
    """True when a ward in an alert category deserves a fresh alert.

    A new alert is due when the ward has never alerted in that category, or
    when the previous alert is older than the cooldown — so a ward stuck at
    HIGH re-alerts periodically, and a ward that recovers and re-escalates
    alerts again as soon as the cooldown lapses."""
    if last_alert_at is None:
        return True
    from datetime import timedelta
    cutoff = now - timedelta(hours=max(cooldown_hours, 0))
    return last_alert_at < cutoff
