from types import SimpleNamespace

import pytest

from app.domain.devices import DeviceRegistrationConflict, validate_device_registration


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
