"""Domain rules for detecting inactive telemetry sources."""

from datetime import datetime, timezone

from .time_rules import require_positive_finite_seconds


def stale_age_seconds(
    status: str,
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
