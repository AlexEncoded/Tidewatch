from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.application.battery_ingestion import ingest_battery_reading, record_battery_reading
from app.domain.devices import DeviceOwnershipError, DeviceSnapshot
from app.domain.battery import BatteryTelemetrySnapshot


MEASURED_AT = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
RECEIVED_AT = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)


def _device(buoy_id: str = "buoy-1") -> DeviceSnapshot:
    return DeviceSnapshot(
        buoy_id=buoy_id,
        device_id="physical-unit-a",
        sensor_channel="A",
        registered_at=MEASURED_AT,
    )


def _reading() -> BatteryTelemetrySnapshot:
    return BatteryTelemetrySnapshot(
        buoy_id="buoy-1",
        battery_percent=80,
        device_id="A",
        measured_at=MEASURED_AT,
        physical_device_id="physical-unit-a",
    )


def test_battery_ingestion_uses_domain_snapshot_and_persists_before_heartbeat() -> None:
    calls = []

    class Reader:
        def get_device_snapshot(self, device_id):
            calls.append(("get_device_snapshot", device_id))
            return _device()

        def add_battery(self, reading):
            calls.append(("add_battery", reading))
            return reading

        def mark_device_seen_by_id(self, device_id, seen_at):
            calls.append(("mark_device_seen_by_id", device_id, seen_at))

    saved = record_battery_reading(Reader(), _reading(), RECEIVED_AT)

    assert saved == _reading()
    assert [call[0] for call in calls] == [
        "get_device_snapshot",
        "add_battery",
        "mark_device_seen_by_id",
    ]
    assert calls[-1] == ("mark_device_seen_by_id", "physical-unit-a", RECEIVED_AT)


@pytest.mark.parametrize(
    ("device", "error", "message"),
    [
        (_device("other-buoy"), DeviceOwnershipError, "Device not found"),
        (
            SimpleNamespace(
                buoy_id="buoy-1", device_id="physical-unit-a", sensor_channel="B"
            ),
            ValueError,
            "channel must match",
        ),
    ],
)
def test_battery_ingestion_rejects_invalid_device_before_persisting(
    device, error, message
) -> None:
    class Reader:
        def get_device_snapshot(self, device_id):
            return device

        def add_battery(self, reading):
            raise AssertionError("invalid device must not persist telemetry")

        def mark_device_seen_by_id(self, device_id, seen_at):
            raise AssertionError("invalid device must not update its heartbeat")

    with pytest.raises(error, match=message):
        record_battery_reading(Reader(), _reading())


def test_battery_ingestion_coordinates_buoy_persistence_device_and_metrics() -> None:
    calls = []

    class Reader:
        def buoy_exists(self, buoy_id):
            calls.append(("buoy_exists", buoy_id))
            return True

        def get_device_snapshot(self, device_id):
            calls.append(("get_device_snapshot", device_id))
            return _device()

        def add_battery(self, reading):
            calls.append(("add_battery", reading))
            return reading

        def mark_device_seen_by_id(self, device_id, seen_at):
            calls.append(("mark_device_seen_by_id", device_id, seen_at))

    class Metrics:
        def record_reading(self, *args):
            calls.append(("record_reading", *args))

    saved = ingest_battery_reading(Reader(), Metrics(), _reading(), RECEIVED_AT)

    assert saved == _reading()
    assert [call[0] for call in calls] == [
        "buoy_exists",
        "get_device_snapshot",
        "add_battery",
        "mark_device_seen_by_id",
        "record_reading",
    ]
    assert calls[-1] == (
        "record_reading",
        "buoy-1",
        80,
        "physical-unit-a",
        "A",
        RECEIVED_AT,
    )


def test_battery_ingestion_skips_metrics_for_unknown_buoy() -> None:
    class Reader:
        def __init__(self):
            self.calls = []

        def buoy_exists(self, buoy_id):
            self.calls.append(("buoy_exists", buoy_id))
            return False

        def add_battery(self, reading):
            raise AssertionError("unknown buoy must not persist telemetry")

    class Metrics:
        def record_reading(self, *args):
            raise AssertionError("unknown buoy must not publish metrics")

    reader = Reader()

    assert ingest_battery_reading(reader, Metrics(), _reading(), RECEIVED_AT) is None
    assert reader.calls == [("buoy_exists", "buoy-1")]
