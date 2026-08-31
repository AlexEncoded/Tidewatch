"""Application service for historical battery analysis."""

from ..domain.battery_analysis import BatterySample, estimate_battery_discharge
from ..models import BatteryAnalysis
from .ports import BatteryTelemetryReader


def analyze_battery_for_buoy(
    reader: BatteryTelemetryReader,
    buoy_id: str,
    device_id: str,
    window: int,
) -> BatteryAnalysis:
    """Run battery analysis through a persistence port."""
    readings = reader.list_batteries(buoy_id, window, device_id)
    estimate = estimate_battery_discharge(
        [
            BatterySample(
                battery_percent=reading.battery_percent,
                measured_at=reading.measured_at,
            )
            for reading in readings
        ]
    )
    return BatteryAnalysis(
        buoy_id=buoy_id,
        device_id=device_id,
        sample_count=estimate.sample_count,
        latest_percent=estimate.latest_percent,
        oldest_percent=estimate.oldest_percent,
        change_percent=estimate.change_percent,
        discharge_rate_percent_per_hour=estimate.discharge_rate_percent_per_hour,
        estimated_hours_remaining=estimate.estimated_hours_remaining,
        confidence=estimate.confidence,
    )
