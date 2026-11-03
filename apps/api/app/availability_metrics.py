"""Initialize Prometheus availability series from registered fleet entities."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .fleet_entities import BuoyEntity, DeviceEntity
from .application.system_ports import AvailabilityMetrics


def _timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def initialize_availability_metrics(
    session: Session, metrics: AvailabilityMetrics
) -> None:
    """Restore all registered buoy and device heartbeat series after startup."""
    buoys = session.execute(select(BuoyEntity.id, BuoyEntity.last_seen_at)).all()
    devices = session.execute(
        select(
            DeviceEntity.buoy_id,
            DeviceEntity.device_id,
            DeviceEntity.sensor_channel,
            DeviceEntity.last_seen_at,
        )
    ).all()

    buoy_timestamps = {
        buoy_id: _timestamp(last_seen_at) for buoy_id, last_seen_at in buoys
    }
    metrics.clear()
    for buoy_id, device_id, sensor_channel, last_seen_at in devices:
        device_timestamp = _timestamp(last_seen_at)
        metrics.record_device_heartbeat(
            buoy_id, device_id, sensor_channel, device_timestamp
        )
        buoy_timestamps[buoy_id] = max(
            buoy_timestamps.get(buoy_id, 0.0), device_timestamp
        )
    for buoy_id, last_seen_timestamp in buoy_timestamps.items():
        metrics.record_buoy_heartbeat(buoy_id, last_seen_timestamp)
