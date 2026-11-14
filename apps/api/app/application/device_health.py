"""Application service for physical-device health summaries."""

from datetime import datetime

from ..domain.device_health import DeviceHealthSnapshot, summarize_device_health
from .device_ports import DeviceHealthReader


def summarize_device_health_for_buoy(
    reader: DeviceHealthReader,
    buoy_id: str,
    now: datetime,
    max_age_seconds: float,
) -> list[DeviceHealthSnapshot]:
    """Load one buoy's devices through the application input port."""
    return summarize_device_health(
        reader.list_device_snapshots(buoy_id), now, max_age_seconds
    )


def get_device_health_for_buoy(
    reader: DeviceHealthReader,
    buoy_id: str,
    now: datetime,
    max_age_seconds: float,
) -> list[DeviceHealthSnapshot] | None:
    """Check buoy existence and return its device health summary."""
    if not reader.buoy_exists(buoy_id):
        return None
    return summarize_device_health_for_buoy(
        reader, buoy_id, now, max_age_seconds
    )
