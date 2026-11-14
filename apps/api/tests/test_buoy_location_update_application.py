from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.application.buoy_location_update import (
    update_buoy_location,
    update_buoy_location_and_publish_movement,
)
from app.domain.buoy import BuoyLocationCommand, BuoySnapshot
from app.domain.location import LocationTelemetrySnapshot


class FakeBuoyLocationUpdater:
    def __init__(self, result):
        self.result = result

    def update_buoy_location(self, buoy_id, command):
        self.buoy_id = buoy_id
        self.command = command
        return self.result


class FakeMovementReader:
    def __init__(self):
        self.buoy_id = None

    def list_locations(self, buoy_id, limit, since=None, until=None):
        self.buoy_id = buoy_id
        self.limit = limit
        return [
            LocationTelemetrySnapshot(
                buoy_id, 36.0, 3.0, datetime(2026, 9, 27, tzinfo=timezone.utc)
            )
        ]


def test_location_update_persists_command_and_recalculates_movement():
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    buoy = BuoySnapshot("TW-123", "Buoy", 36.2, 3.1, "active", now, now)
    updater = FakeBuoyLocationUpdater(buoy)
    reader = FakeMovementReader()
    command = BuoyLocationCommand(36.2, 3.1)

    result = update_buoy_location(updater, reader, "TW-123", command)

    assert result.buoy is buoy
    assert updater.command == command
    assert reader.buoy_id == "TW-123"
    assert reader.limit == 50
    assert result.movement.buoy_id == "TW-123"


def test_location_update_does_not_analyze_unknown_buoy():
    updater = FakeBuoyLocationUpdater(None)
    reader = FakeMovementReader()

    assert update_buoy_location(
        updater, reader, "missing", BuoyLocationCommand(1.0, 2.0)
    ) is None
    assert reader.buoy_id is None


def test_location_update_publishes_movement_through_metrics_port(monkeypatch):
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    buoy = BuoySnapshot("TW-123", "Buoy", 36.2, 3.1, "active", now, now)
    updater = FakeBuoyLocationUpdater(buoy)
    reader = FakeMovementReader()
    monkeypatch.setattr(
        "app.application.buoy_location_update.analyze_movement_for_buoy",
        lambda *_args: SimpleNamespace(
            buoy_id="TW-123", sample_count=2, average_speed_mps=1.25
        ),
    )

    class Metrics:
        def __init__(self):
            self.events = []

        def record_buoy_movement(self, buoy_id, speed_mps):
            self.events.append((buoy_id, speed_mps))

    metrics = Metrics()
    result = update_buoy_location_and_publish_movement(
        updater,
        reader,
        metrics,
        "TW-123",
        BuoyLocationCommand(36.2, 3.1),
    )

    assert result is not None
    assert metrics.events == [("TW-123", 1.25)]


@pytest.mark.parametrize(
    "latitude, longitude",
    [(90.01, 0), (-90.01, 0), (0, 180.01), (0, -180.01)],
)
def test_location_command_rejects_coordinates_outside_domain_bounds(
    latitude, longitude
):
    with pytest.raises(ValueError):
        BuoyLocationCommand(latitude, longitude)
