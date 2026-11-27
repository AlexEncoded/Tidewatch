"""Domain rules for the physical devices assigned to a buoy."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from ..shared.device import (
    DEVICE_FIRMWARE_MAX_LENGTH,
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    SENSOR_ID_MAX_LENGTH,
    SensorChannel,
    VALID_SENSOR_CHANNELS,
)

DeviceSensorChannel = SensorChannel
DeviceOperationalStatus = Literal["active", "maintenance", "inactive"]


def resolve_telemetry_device_id(
    reading_device_id: str | None,
    batch_device_id: str | None,
) -> str | None:
    """Prefer an explicit reading owner, falling back to the batch device."""
    return reading_device_id if reading_device_id is not None else batch_device_id


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
    sensor_channel: DeviceSensorChannel
    registered_at: datetime
    firmware_version: str | None = None
    status: DeviceOperationalStatus = "active"
    last_seen_at: datetime | None = None


def validate_device_ownership(device: DeviceSnapshot | None, buoy_id: str) -> None:
    """Ensure a telemetry device belongs to the buoy receiving the data."""
    if device is None or device.buoy_id != buoy_id:
        raise DeviceOwnershipError("Device not found")


def validate_telemetry_device_channel(
    device: DeviceSnapshot,
    channels: Iterable[SensorChannel],
    telemetry_name: str = "Telemetry",
) -> None:
    """Ensure all telemetry channels match their registered physical device."""
    if any(channel != device.sensor_channel for channel in channels):
        raise ValueError(
            f"{telemetry_name} channel must match physical device channel "
            f"{device.sensor_channel}"
        )


def validate_device_registration(
    device_id: str,
    sensor_channel: SensorChannel,
    existing_devices: Iterable[DeviceSnapshot],
    existing_registered_device: DeviceSnapshot | None = None,
) -> None:
    """Validate uniqueness of a device and its redundant sensor channel."""
    if (
        existing_registered_device is not None
        and existing_registered_device.device_id == device_id
    ):
        raise DeviceRegistrationConflict("Device already registered")
    devices = list(existing_devices)
    if any(device.device_id == device_id for device in devices):
        raise DeviceRegistrationConflict("Device already registered")
    if any(device.sensor_channel == sensor_channel for device in devices):
        raise DeviceRegistrationConflict("Sensor channel already registered")
