"""Application query for fleet-wide location history."""

from datetime import datetime

from ..domain.telemetry import LocationTelemetrySnapshot
from .ports import FleetLocationReader


def list_fleet_locations(
    reader: FleetLocationReader,
    limit: int,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[LocationTelemetrySnapshot]:
    """Read fleet location snapshots through the application port."""
    return reader.list_all_locations(limit, since, until)
