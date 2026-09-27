from datetime import datetime, timezone

from app.application.buoy_locations import list_buoy_locations
from app.domain.telemetry import LocationTelemetrySnapshot


class FakeBuoyLocationHistoryReader:
    def __init__(self, exists=True):
        self.exists = exists
        self.query = None

    def buoy_exists(self, buoy_id):
        self.checked_buoy_id = buoy_id
        return self.exists

    def list_locations(self, buoy_id, limit, since=None, until=None):
        self.query = (buoy_id, limit, since, until)
        measured_at = since or datetime.now(timezone.utc)
        return [LocationTelemetrySnapshot(buoy_id, 12.0, 23.0, measured_at)]


def test_buoy_location_query_validates_existence_and_forwards_filters():
    reader = FakeBuoyLocationHistoryReader()
    since = datetime(2026, 9, 1, tzinfo=timezone.utc)
    until = datetime(2026, 9, 27, tzinfo=timezone.utc)

    locations = list_buoy_locations(reader, "TW-123", 25, since, until)

    assert reader.checked_buoy_id == "TW-123"
    assert reader.query == ("TW-123", 25, since, until)
    assert len(locations) == 1


def test_buoy_location_query_returns_none_for_unknown_buoy_without_listing():
    reader = FakeBuoyLocationHistoryReader(exists=False)

    assert list_buoy_locations(reader, "missing", 25) is None
    assert reader.query is None
