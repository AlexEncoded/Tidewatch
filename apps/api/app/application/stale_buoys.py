"""Application query for buoys that have stopped reporting."""

from datetime import datetime, timezone

from ..domain.buoy import StaleBuoySnapshot
from ..domain.staleness import stale_age_seconds
from .ports import StaleBuoyReader


def find_stale_buoys(
    reader: StaleBuoyReader,
    max_age_seconds: float,
    now: datetime | None = None,
) -> list[StaleBuoySnapshot]:
    """Find active buoys whose last activity is older than the configured age."""
    reference_time = now or datetime.now(timezone.utc)
    stale: list[StaleBuoySnapshot] = []
    for buoy in reader.list_buoy_activity():
        age_seconds = stale_age_seconds(
            buoy.status, buoy.last_seen_at, max_age_seconds, reference_time
        )
        if age_seconds is None or buoy.last_seen_at is None:
            continue
        last_seen_at = (
            buoy.last_seen_at.replace(tzinfo=timezone.utc)
            if buoy.last_seen_at.tzinfo is None
            else buoy.last_seen_at
        )
        stale.append(
            StaleBuoySnapshot(
                buoy_id=buoy.buoy_id,
                name=buoy.name,
                status=buoy.status,
                last_seen_at=last_seen_at,
                age_seconds=round(age_seconds, 2),
            )
        )
    return stale
