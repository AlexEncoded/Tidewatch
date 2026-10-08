"""Domain rules for the physical devices assigned to a buoy."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .telemetry_types import (
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    FIRMWARE_VERSION_MAX_LENGTH,
    SensorChannel,
)

DeviceSensorChannel = SensorChannel
DeviceOperationalStatus = Literal["active", "maintenance", "inactive"]
DEVICE_FIRMWARE_MAX_LENGTH = FIRMWARE_VERSION_MAX_LENGTH


class DeviceRegistrationConflict(ValueError):
    """Raised when a device registration violates a buoy invariant."""


class DeviceOwnershipError(ValueError):
    """Raised when telemetry references an unknown or foreign device."""


@dataclass(frozen=True)
class DeviceRegistrationCommand:
    """Domain input for registering a physical device."""

    device_id: str
    sensor_channel: DeviceSensorChannel
    firmware_version: str | None = None

    def __post_init__(self) -> None:
        if not DEVICE_ID_MIN_LENGTH <= len(self.device_id) <= DEVICE_ID_MAX_LENGTH:
            raise ValueError(
                f"Device ID must contain between {DEVICE_ID_MIN_LENGTH} "
                f"and {DEVICE_ID_MAX_LENGTH} characters"
            )
        if self.sensor_channel not in ("A", "B"):
            raise ValueError("Device sensor channel must be A or B")
        if (
            self.firmware_version is not None
            and len(self.firmware_version) > DEVICE_FIRMWARE_MAX_LENGTH
        ):
            raise ValueError(
                f"Firmware version must contain at most {DEVICE_FIRMWARE_MAX_LENGTH} characters"
            )


@dataclass(frozen=True)
class DeviceStatusCommand:
    """Domain input for changing a device operational status."""

    status: DeviceOperationalStatus

    def __post_init__(self) -> None:
        if self.status not in ("active", "maintenance", "inactive"):
            raise ValueError(f"Unsupported device status {self.status!r}")


@dataclass(frozen=True)
class DeviceSnapshot:
    """Domain view of a registered physical device."""

    buoy_id: str
    device_id: str
    sensor_channel: str
    registered_at: datetime
    firmware_version: str | None = None
    status: str = "active"
    last_seen_at: datetime | None = None


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
