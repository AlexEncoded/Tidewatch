"""Domain rules for detecting inactive telemetry sources."""

from datetime import datetime, timezone

from .buoy import BuoyActivitySnapshot, BuoyOperationalStatus, StaleBuoySnapshot
from .time_rules import require_positive_finite_seconds


def stale_age_seconds(
    status: BuoyOperationalStatus,
    last_seen_at: datetime | None,
    max_age_seconds: float,
    now: datetime,
) -> float | None:
    """Return the age of an active buoy when it exceeds the configured limit."""
    require_positive_finite_seconds(max_age_seconds, "Maximum buoy age")
    if status != "active" or last_seen_at is None:
        return None
    reference = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
    last_seen = (
        last_seen_at.replace(tzinfo=timezone.utc)
        if last_seen_at.tzinfo is None
        else last_seen_at
    )
    age_seconds = (reference - last_seen).total_seconds()
    return age_seconds if age_seconds > max_age_seconds else None


def classify_stale_buoy(
    buoy: BuoyActivitySnapshot,
    max_age_seconds: float,
    now: datetime,
) -> StaleBuoySnapshot | None:
    """Build a stale-buoy snapshot when an active buoy exceeds its age limit."""
    age_seconds = stale_age_seconds(
        buoy.status, buoy.last_seen_at, max_age_seconds, now
    )
    if age_seconds is None or buoy.last_seen_at is None:
        return None
    last_seen_at = (
        buoy.last_seen_at.replace(tzinfo=timezone.utc)
        if buoy.last_seen_at.tzinfo is None
        else buoy.last_seen_at
    )
    return StaleBuoySnapshot(
        buoy_id=buoy.buoy_id,
        name=buoy.name,
        status=buoy.status,
        last_seen_at=last_seen_at,
        age_seconds=round(age_seconds, 2),
    )
