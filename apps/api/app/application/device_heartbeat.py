"""Application service for recording device telemetry heartbeats."""

from datetime import datetime, timezone
from collections.abc import Iterable
from typing import Protocol

from ..domain.devices import DeviceSnapshot, DeviceOwnershipError, validate_device_ownership


class DeviceHeartbeatRegistry(Protocol):
    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        ...

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        ...


def record_device_heartbeat(
    registry: DeviceHeartbeatRegistry,
    buoy_id: str,
    device_id: str,
    seen_at: datetime | None = None,
    sensor_channels: Iterable[str] = (),
) -> tuple[DeviceSnapshot, datetime]:
    """Validate device ownership and channels before persisting its heartbeat."""
    device = registry.get_device_snapshot(device_id)
    validate_device_ownership(device, buoy_id)
    if any(channel != device.sensor_channel for channel in sensor_channels):
        raise ValueError(
            f"Telemetry channel must match physical device channel "
            f"{device.sensor_channel}"
        )
    timestamp = seen_at or datetime.now(timezone.utc)
    updated = registry.mark_device_seen_by_id(device_id, timestamp)
    if updated is None:
        raise DeviceOwnershipError("Device not found")
    return updated, timestamp
