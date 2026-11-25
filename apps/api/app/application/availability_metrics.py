"""Restore availability metrics from application-level fleet snapshots."""

from datetime import datetime, timezone
from typing import Iterable

from ..domain.fleet.buoy import BuoySnapshot
from ..domain.fleet.devices import DeviceSnapshot
from .system_ports import AvailabilityMetrics


def _timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def initialize_availability_metrics(
    buoys: Iterable[BuoySnapshot],
    devices: Iterable[DeviceSnapshot],
    metrics: AvailabilityMetrics,
) -> None:
    """Restore buoy and device heartbeat series without storage dependencies."""
    buoy_timestamps = {
        buoy.buoy_id: _timestamp(buoy.last_seen_at) for buoy in buoys
    }
    metrics.clear()
    for device in devices:
        device_timestamp = _timestamp(device.last_seen_at)
        metrics.restore_device_heartbeat(
            device.buoy_id,
            device.device_id,
            device.sensor_channel,
            device_timestamp,
        )
        buoy_timestamps[device.buoy_id] = max(
            buoy_timestamps.get(device.buoy_id, 0.0), device_timestamp
        )
    for buoy_id, last_seen_timestamp in buoy_timestamps.items():
        metrics.restore_buoy_heartbeat(buoy_id, last_seen_timestamp)
