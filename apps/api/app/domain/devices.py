"""Domain rules for the physical devices assigned to a buoy."""

from collections.abc import Iterable


class DeviceRegistrationConflict(ValueError):
    """Raised when a device registration violates a buoy invariant."""


def validate_device_registration(
    device_id: str,
    sensor_channel: str,
    existing_devices: Iterable[object],
) -> None:
    """Validate uniqueness of a device and its redundant sensor channel."""
    devices = list(existing_devices)
    if any(getattr(device, "device_id", None) == device_id for device in devices):
        raise DeviceRegistrationConflict("Device already registered")
    if any(getattr(device, "sensor_channel", None) == sensor_channel for device in devices):
        raise DeviceRegistrationConflict("Sensor channel already registered")
