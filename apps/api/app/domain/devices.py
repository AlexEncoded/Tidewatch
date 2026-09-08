"""Domain rules for the physical devices assigned to a buoy."""

from collections.abc import Iterable


class DeviceRegistrationConflict(ValueError):
    """Raised when a device registration violates a buoy invariant."""


class DeviceOwnershipError(ValueError):
    """Raised when telemetry references an unknown or foreign device."""


def validate_device_ownership(device: object | None, buoy_id: str) -> None:
    """Ensure a telemetry device belongs to the buoy receiving the data."""
    if device is None or getattr(device, "buoy_id", None) != buoy_id:
        raise DeviceOwnershipError("Device not found")


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
