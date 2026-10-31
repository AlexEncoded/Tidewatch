"""Application service for historical temperature analysis."""

from ..domain.temperature import (
    TemperatureAnalysisSnapshot,
    analyze_temperature_samples,
    valid_temperature_readings,
)
from .sensor_ports import TemperatureTelemetryReader


def list_valid_temperature_readings(
    reader: TemperatureTelemetryReader,
    buoy_id: str,
    window: int,
) -> list:
    """Read a temperature window while excluding invalid telemetry."""
    return valid_temperature_readings(reader.list_temperatures(buoy_id, window))


def analyze_temperature_readings(
    buoy_id: str,
    readings: list,
    threshold: float,
) -> TemperatureAnalysisSnapshot:
    """Map valid temperature readings into the public analysis contract."""
    return analyze_temperature_samples(buoy_id, readings, threshold)


def analyze_temperature_for_buoy(
    reader: TemperatureTelemetryReader,
    buoy_id: str,
    window: int,
    threshold: float,
) -> TemperatureAnalysisSnapshot:
    """Run temperature analysis through a persistence port."""
    return analyze_temperature_readings(
        buoy_id,
        list_valid_temperature_readings(reader, buoy_id, window),
        threshold,
    )
