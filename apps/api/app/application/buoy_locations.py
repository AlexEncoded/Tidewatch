"""Application queries for a buoy's location history."""

from datetime import datetime

from ..domain.location import LocationTelemetrySnapshot
from .fleet_ports import BuoyLocationHistoryReader
from .location_queries import (
    InvalidLocationTimeRange as InvalidBuoyLocationTimeRange,
    validate_location_time_range,
)


def list_buoy_locations(
    reader: BuoyLocationHistoryReader,
    buoy_id: str,
    limit: int,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[LocationTelemetrySnapshot] | None:
    """Return filtered location history, or ``None`` if the buoy is unknown."""
    validate_location_time_range(since, until)
    if not reader.buoy_exists(buoy_id):
        return None
    return reader.list_locations(buoy_id, limit, since, until)
