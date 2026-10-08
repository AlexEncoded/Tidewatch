"""Application service for physical-device health summaries."""

from collections.abc import Sequence
from datetime import datetime

from ..domain.device_health import DeviceHealthSnapshot, assess_device_liveness
from .ports import DeviceHealthReader


def summarize_device_health_for_buoy(
    reader: DeviceHealthReader,
    buoy_id: str,
    now: datetime,
    max_age_seconds: float,
) -> list[DeviceHealthSnapshot]:
    """Load one buoy's devices through the application input port."""
    return summarize_device_health(reader.list_devices(buoy_id), now, max_age_seconds)


def summarize_device_health(
    devices: Sequence[object],
    now: datetime,
    max_age_seconds: float,
) -> list[DeviceHealthSnapshot]:
    """Map persisted device state and heartbeats into operational health."""
    summaries: list[DeviceHealthSnapshot] = []
    for device in devices:
        status = device.status
        liveness = assess_device_liveness(
            status,
            getattr(device, "last_seen_at", None),
            now,
            max_age_seconds,
        )
        summaries.append(
            DeviceHealthSnapshot(
                buoy_id=device.buoy_id,
                device_id=device.device_id,
                sensor_channel=device.sensor_channel,
                status=status,
                last_seen_at=liveness.last_seen_at,
                age_seconds=liveness.age_seconds,
                is_stale=liveness.is_stale,
            )
        )
    return summaries
