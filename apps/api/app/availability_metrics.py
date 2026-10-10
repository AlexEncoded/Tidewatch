"""Initialize Prometheus availability series from registered fleet entities."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .entities import BuoyEntity, DeviceEntity
from .metrics import buoy_last_seen_timestamp_seconds, device_last_seen_timestamp_seconds


def _timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def initialize_availability_metrics(session: Session) -> None:
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
    buoy_last_seen_timestamp_seconds.clear()
    device_last_seen_timestamp_seconds.clear()
    for buoy_id, device_id, sensor_channel, last_seen_at in devices:
        device_timestamp = _timestamp(last_seen_at)
        device_last_seen_timestamp_seconds.labels(
            buoy_id=buoy_id,
            device_id=device_id,
            sensor_channel=sensor_channel,
        ).set(device_timestamp)
        buoy_timestamps[buoy_id] = max(
            buoy_timestamps.get(buoy_id, 0.0), device_timestamp
        )
    for buoy_id, last_seen_timestamp in buoy_timestamps.items():
        buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(
            last_seen_timestamp
        )
