"""Application query for fleet-wide location history."""

from datetime import datetime

from ..domain.location import LocationTelemetrySnapshot
from .fleet_ports import FleetLocationReader
from .location_queries import validate_location_time_range


def list_fleet_locations(
    reader: FleetLocationReader,
    limit: int,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[LocationTelemetrySnapshot]:
    """Read fleet location snapshots through the application port."""
    validate_location_time_range(since, until)
    return reader.list_all_locations(limit, since, until)
