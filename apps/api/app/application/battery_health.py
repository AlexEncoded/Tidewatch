"""Application service for redundant battery health."""

from datetime import datetime, timezone

from ..domain.battery_health import estimate_battery_health
from ..models import BatteryHealth
from .ports import BatteryTelemetryReader


def analyze_battery_health_for_buoy(
    reader: BatteryTelemetryReader,
    buoy_id: str,
    threshold: float,
) -> BatteryHealth:
    """Evaluate both battery devices through the persistence port."""
    readings = {
        device_id: reader.latest_battery(buoy_id, device_id)
        for device_id in ("A", "B")
    }
    estimate = estimate_battery_health(
        readings["A"].battery_percent if readings["A"] else None,
        readings["B"].battery_percent if readings["B"] else None,
        threshold,
    )
    return BatteryHealth(
        buoy_id=buoy_id,
        status=estimate.status,
        device_a_percent=estimate.device_a_percent,
        device_b_percent=estimate.device_b_percent,
        delta_percent=estimate.delta_percent,
        degraded_devices=estimate.degraded_devices or [],
        checked_at=datetime.now(timezone.utc),
    )
