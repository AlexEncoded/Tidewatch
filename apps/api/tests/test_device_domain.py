from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.domain.devices import (
    DeviceOwnershipError,
    DeviceRegistrationConflict,
    validate_device_ownership,
    validate_device_registration,
)
from app.domain.staleness import stale_age_seconds
from app.application.device_registration import register_device
from app.application.device_status import update_device_status
from app.application.device_heartbeat import record_device_heartbeat


def test_device_registration_accepts_the_other_redundant_channel() -> None:
    validate_device_registration(
        "device-b",
        "B",
        [SimpleNamespace(device_id="device-a", sensor_channel="A")],
    )


def test_device_ownership_accepts_device_from_target_buoy() -> None:
    validate_device_ownership(SimpleNamespace(buoy_id="buoy-1"), "buoy-1")


@pytest.mark.parametrize("device", [None, SimpleNamespace(buoy_id="other-buoy")])
def test_device_ownership_rejects_unknown_or_foreign_device(device) -> None:
    with pytest.raises(DeviceOwnershipError, match="Device not found"):
        validate_device_ownership(device, "buoy-1")


@pytest.mark.parametrize(
    ("device_id", "sensor_channel", "message"),
    [
        ("device-a", "B", "Device already registered"),
        ("device-b", "A", "Sensor channel already registered"),
    ],
)
def test_device_registration_rejects_conflicts(device_id: str, sensor_channel: str, message: str) -> None:
    with pytest.raises(DeviceRegistrationConflict, match=message):
        validate_device_registration(
            device_id,
            sensor_channel,
            [SimpleNamespace(device_id="device-a", sensor_channel="A")],
        )


def test_register_device_application_service_uses_registry() -> None:
    class Registry:
        def __init__(self):
            self.created = None

        def get_device(self, device_id):
            return None

        def list_devices(self, buoy_id):
            return []

        def create_device(self, buoy_id, device):
            self.created = (buoy_id, device)
            return self.created

    device = SimpleNamespace(device_id="device-a", sensor_channel="A")
    registry = Registry()

    result = register_device(registry, "buoy-1", device)

    assert result == ("buoy-1", device)


@pytest.mark.parametrize(
    ("existing", "message"),
    [
        ([SimpleNamespace(device_id="device-a", sensor_channel="A")], "Device already registered"),
        ([SimpleNamespace(device_id="device-b", sensor_channel="A")], "Sensor channel already registered"),
    ],
)
def test_register_device_application_service_rejects_conflicts(existing, message: str) -> None:
    class Registry:
        def get_device(self, device_id):
            return existing[0] if existing[0].device_id == device_id else None

        def list_devices(self, buoy_id):
            return existing

        def create_device(self, buoy_id, device):
            raise AssertionError("conflicting registrations must not be persisted")

    device_id = existing[0].device_id if message == "Device already registered" else "device-c"
    device = SimpleNamespace(device_id=device_id, sensor_channel="A")

    with pytest.raises(DeviceRegistrationConflict, match=message):
        register_device(Registry(), "buoy-1", device)


def test_update_device_status_application_service_returns_updated_device() -> None:
    class Registry:
        def update_device_status(self, buoy_id, device_id, update):
            return SimpleNamespace(device_id=device_id, status=update.status)

    update = SimpleNamespace(status="maintenance")

    result = update_device_status(Registry(), "buoy-1", "device-a", update)

    assert result.device_id == "device-a"
    assert result.status == "maintenance"


def test_update_device_status_application_service_rejects_missing_device() -> None:
    class Registry:
        def update_device_status(self, buoy_id, device_id, update):
            return None

    with pytest.raises(DeviceOwnershipError, match="Device not found"):
        update_device_status(Registry(), "buoy-1", "missing", SimpleNamespace(status="active"))


def test_record_device_heartbeat_updates_registry_with_supplied_time() -> None:
    class Registry:
        def get_device(self, device_id):
            return SimpleNamespace(device_id=device_id, buoy_id="buoy-1")

        def mark_device_seen(self, device, seen_at):
            return SimpleNamespace(device_id=device.device_id, last_seen_at=seen_at)

    seen_at = datetime(2026, 9, 8, tzinfo=timezone.utc)
    device, timestamp = record_device_heartbeat(Registry(), "buoy-1", "device-a", seen_at)

    assert timestamp == seen_at
    assert device.last_seen_at == seen_at


def test_record_device_heartbeat_rejects_foreign_device() -> None:
    class Registry:
        def get_device(self, device_id):
            return SimpleNamespace(device_id=device_id, buoy_id="other-buoy")

        def mark_device_seen(self, device, seen_at):
            raise AssertionError("foreign devices must not update their heartbeat")

    with pytest.raises(DeviceOwnershipError, match="Device not found"):
        record_device_heartbeat(Registry(), "buoy-1", "device-a")


def test_stale_age_seconds_returns_age_only_after_threshold() -> None:
    now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)

    assert stale_age_seconds("active", now - timedelta(seconds=61), 60, now) == 61
    assert stale_age_seconds("active", now - timedelta(seconds=60), 60, now) is None


def test_stale_age_seconds_ignores_inactive_or_never_seen_buoys() -> None:
    now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)

    assert stale_age_seconds("maintenance", now - timedelta(hours=1), 60, now) is None
    assert stale_age_seconds("active", None, 60, now) is None
