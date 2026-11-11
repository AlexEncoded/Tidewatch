"""Application queries for a buoy's location history."""

from datetime import datetime

from ..domain.location import LocationTelemetrySnapshot
from .fleet_ports import BuoyLocationHistoryReader


class InvalidBuoyLocationTimeRange(ValueError):
    """The start of a location history range is later than its end."""


def list_buoy_locations(
    reader: BuoyLocationHistoryReader,
    buoy_id: str,
    limit: int,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[LocationTelemetrySnapshot] | None:
    """Return filtered location history, or ``None`` if the buoy is unknown."""
    if since is not None and until is not None and since > until:
        raise InvalidBuoyLocationTimeRange(
            "since must be earlier than or equal to until"
        )
    if not reader.buoy_exists(buoy_id):
        return None
    return reader.list_locations(buoy_id, limit, since, until)
