from types import SimpleNamespace

import pytest

from app.domain.devices import DeviceRegistrationConflict, validate_device_registration
from app.application.device_registration import register_device


def test_device_registration_accepts_the_other_redundant_channel() -> None:
    validate_device_registration(
        "device-b",
        "B",
        [SimpleNamespace(device_id="device-a", sensor_channel="A")],
    )


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
