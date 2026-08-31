"""Application service for historical temperature analysis."""

from ..domain.temperature import estimate_temperature
from ..models import TemperatureAnalysis
from .ports import TemperatureTelemetryReader


def analyze_temperature_for_buoy(
    reader: TemperatureTelemetryReader,
    buoy_id: str,
    window: int,
    threshold: float,
) -> TemperatureAnalysis:
    """Run temperature analysis through a persistence port."""
    readings = [
        reading
        for reading in reader.list_temperatures(buoy_id, window)
        if reading.quality != "invalid"
    ]
    estimate = estimate_temperature(
        [reading.temperature_celsius for reading in readings], threshold
    )
    return TemperatureAnalysis(
        buoy_id=buoy_id,
        sample_count=estimate.sample_count,
        latest_temperature=estimate.latest_temperature,
        average_temperature=estimate.average_temperature,
        minimum_temperature=estimate.minimum_temperature,
        maximum_temperature=estimate.maximum_temperature,
        change_celsius=estimate.change_celsius,
        trend=estimate.trend,
        is_anomaly=estimate.is_anomaly,
        anomaly_reason=estimate.anomaly_reason,
    )
