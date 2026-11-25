"""Application service for redundant battery health."""

from datetime import datetime, timezone

from ..domain.sensors.battery_health import BatteryHealthSnapshot, estimate_battery_health
from .battery_ports import BatteryMetrics, BatteryTelemetryReader


def analyze_battery_health_for_buoy(
    reader: BatteryTelemetryReader,
    buoy_id: str,
    threshold: float,
) -> BatteryHealthSnapshot:
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
    return BatteryHealthSnapshot(
        buoy_id=buoy_id,
        status=estimate.status,
        device_a_percent=estimate.device_a_percent,
        device_b_percent=estimate.device_b_percent,
        delta_percent=estimate.delta_percent,
        degraded_devices=estimate.degraded_devices,
        checked_at=datetime.now(timezone.utc),
    )


def evaluate_battery_health_for_buoy(
    reader: BatteryTelemetryReader,
    metrics: BatteryMetrics,
    buoy_id: str,
    threshold: float,
) -> BatteryHealthSnapshot | None:
    """Validate, evaluate, and publish a buoy's redundant battery health."""
    if not reader.buoy_exists(buoy_id):
        return None

    result = analyze_battery_health_for_buoy(reader, buoy_id, threshold)
    metrics.record_health(
        buoy_id,
        result.device_a_percent,
        result.device_b_percent,
        result.delta_percent,
    )
    return result
