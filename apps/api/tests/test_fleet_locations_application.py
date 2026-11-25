from datetime import datetime, timezone

import pytest

from app.application.fleet_locations import list_fleet_locations
from app.application.location_queries import InvalidLocationTimeRange
from app.domain.fleet.location import LocationTelemetrySnapshot


class FakeFleetLocationReader:
    def __init__(self) -> None:
        self.query = None

    def list_all_locations(self, limit, since=None, until=None):
        self.query = (limit, since, until)
        return [
            LocationTelemetrySnapshot(
                buoy_id="buoy-1",
                latitude=12.0,
                longitude=23.0,
                measured_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
            )
        ]


def test_fleet_location_query_delegates_filters_to_reader_port() -> None:
    reader = FakeFleetLocationReader()
    since = datetime(2026, 9, 1, tzinfo=timezone.utc)
    until = datetime(2026, 9, 26, tzinfo=timezone.utc)

    locations = list_fleet_locations(reader, 100, since, until)

    assert reader.query == (100, since, until)
    assert len(locations) == 1
    assert locations[0].buoy_id == "buoy-1"


def test_fleet_location_query_rejects_invalid_range_before_reader_call() -> None:
    reader = FakeFleetLocationReader()
    since = datetime(2026, 9, 26, tzinfo=timezone.utc)
    until = datetime(2026, 9, 1, tzinfo=timezone.utc)

    with pytest.raises(InvalidLocationTimeRange):
        list_fleet_locations(reader, 100, since, until)

    assert reader.query is None
