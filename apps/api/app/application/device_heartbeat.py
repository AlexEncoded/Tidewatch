"""Application service for recording device telemetry heartbeats."""

from datetime import datetime, timezone
from typing import Protocol

from ..domain.devices import validate_device_ownership


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
):
    """Validate ownership and persist the latest device heartbeat."""
    device = registry.get_device(device_id)
    validate_device_ownership(device, buoy_id)
    timestamp = seen_at or datetime.now(timezone.utc)
    return registry.mark_device_seen(device, timestamp), timestamp
