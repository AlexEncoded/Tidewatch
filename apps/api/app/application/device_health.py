"""Application service for physical-device health summaries."""

from collections.abc import Sequence
from datetime import datetime, timezone

from ..models import DeviceHealth
from .ports import DeviceHealthReader


def summarize_device_health_for_buoy(
    reader: DeviceHealthReader,
    buoy_id: str,
    now: datetime,
    max_age_seconds: float,
) -> list[DeviceHealth]:
    """Load one buoy's devices through the application input port."""
    return summarize_device_health(reader.list_devices(buoy_id), now, max_age_seconds)


def summarize_device_health(
    devices: Sequence[object],
    now: datetime,
    max_age_seconds: float,
) -> list[DeviceHealth]:
    """Map persisted device state and heartbeats into operational health."""
    reference = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
    summaries: list[DeviceHealth] = []
    for device in devices:
        last_seen = getattr(device, "last_seen_at", None)
        normalized_last_seen = None
        age_seconds = None
        if last_seen is not None:
            normalized_last_seen = (
                last_seen.replace(tzinfo=timezone.utc)
                if last_seen.tzinfo is None
                else last_seen
            )
            age_seconds = max(
                0.0, (reference - normalized_last_seen).total_seconds()
            )
        status = device.status
        summaries.append(
            DeviceHealth(
                buoy_id=device.buoy_id,
                device_id=device.device_id,
                sensor_channel=device.sensor_channel,
                status=status,
                last_seen_at=normalized_last_seen,
                age_seconds=round(age_seconds, 2) if age_seconds is not None else None,
                is_stale=(
                    status == "active"
                    and (age_seconds is None or age_seconds > max_age_seconds)
                ),
            )
        )
    return summaries
