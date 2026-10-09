"""Application service for recording device telemetry heartbeats."""

from datetime import datetime, timezone
from collections.abc import Iterable
from typing import Protocol

from ..domain.devices import DeviceSnapshot, validate_device_ownership
from .device_snapshots import to_device_snapshot


class DeviceHeartbeatRegistry(Protocol):
    def get_device(self, device_id: str):
        ...

    def mark_device_seen(self, device, seen_at: datetime):
        ...


def record_device_heartbeat(
    registry: DeviceHeartbeatRegistry,
    buoy_id: str,
    device_id: str,
    seen_at: datetime | None = None,
    sensor_channels: Iterable[str] = (),
) -> tuple[DeviceSnapshot, datetime]:
    """Validate device ownership and channels before persisting its heartbeat."""
    device = registry.get_device(device_id)
    validate_device_ownership(device, buoy_id)
    if any(channel != device.sensor_channel for channel in sensor_channels):
        raise ValueError(
            f"Telemetry channel must match physical device channel "
            f"{device.sensor_channel}"
        )
    timestamp = seen_at or datetime.now(timezone.utc)
    updated = registry.mark_device_seen(device, timestamp)
    return to_device_snapshot(updated), timestamp
