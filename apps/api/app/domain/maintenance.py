from datetime import datetime, timezone
from typing import Literal


BatterySeverity = Literal["warning", "critical"]


def low_battery_severity(battery_percent: float) -> BatterySeverity | None:
    """Return the maintenance severity for a battery reading, if it is low."""
    if battery_percent < 10:
        return "critical"
    if battery_percent < 20:
        return "warning"
    return None


def is_buoy_silent(
    status: str,
    last_seen_at: datetime | None,
    now: datetime,
    max_age_seconds: float,
) -> bool:
    """Return whether an active buoy has exceeded its telemetry age limit."""
    if status != "active" or last_seen_at is None:
        return False
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - last_seen_at).total_seconds() > max_age_seconds
