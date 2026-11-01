"""Application query for buoys that have stopped reporting."""

from datetime import datetime, timezone

from ..domain.buoy import StaleBuoySnapshot
from ..domain.staleness import classify_stale_buoy
from .fleet_ports import StaleBuoyReader


def find_stale_buoys(
    reader: StaleBuoyReader,
    max_age_seconds: float,
    now: datetime | None = None,
) -> list[StaleBuoySnapshot]:
    """Find active buoys whose last activity is older than the configured age."""
    reference_time = now or datetime.now(timezone.utc)
    stale = (
        classify_stale_buoy(buoy, max_age_seconds, reference_time)
        for buoy in reader.list_buoy_activity()
    )
    return [buoy for buoy in stale if buoy is not None]
