from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.application.battery_ingestion import record_battery_reading
from app.domain.devices import DeviceOwnershipError, DeviceSnapshot
from app.domain.telemetry import BatteryTelemetrySnapshot


MEASURED_AT = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)


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

    saved = record_battery_reading(Reader(), _reading())

    assert saved == _reading()
    assert [call[0] for call in calls] == [
        "get_device_snapshot",
        "add_battery",
        "mark_device_seen_by_id",
    ]


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
