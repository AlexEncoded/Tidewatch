"""Application service for the pressure-analysis use case."""

from typing import Protocol

from ..domain.pressure import estimate_pressure
from ..models import PressureAnalysis


class PressureTelemetryReader(Protocol):
    def list_pressures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list:
        ...


def analyze_pressure_for_buoy(
    reader: PressureTelemetryReader,
    buoy_id: str,
    window: int,
) -> PressureAnalysis:
    """Run pressure analysis through a persistence port."""
    readings = [
        reading
        for reading in reader.list_pressures(buoy_id, window)
        if reading.quality != "invalid"
    ]
    estimate = estimate_pressure([reading.pressure_kpa for reading in readings])
    return PressureAnalysis(
        buoy_id=buoy_id,
        sample_count=estimate.sample_count,
        latest_pressure_kpa=estimate.latest_pressure_kpa,
        average_pressure_kpa=estimate.average_pressure_kpa,
        minimum_pressure_kpa=estimate.minimum_pressure_kpa,
        maximum_pressure_kpa=estimate.maximum_pressure_kpa,
        pressure_range_kpa=estimate.pressure_range_kpa,
        estimated_wave_height_m=estimate.estimated_wave_height_m,
        confidence=estimate.confidence,
        sea_state=estimate.sea_state,
    )
