"""Application service for the experimental wave-analysis use case."""

from typing import Protocol

from ..analytics import analyze_wave
from ..models import WaveAnalysis


class WaveTelemetryReader(Protocol):
    def list_imu(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_locations(self, buoy_id: str, limit: int) -> list:
        ...


def analyze_wave_for_buoy(
    reader: WaveTelemetryReader,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
) -> WaveAnalysis:
    """Run wave analysis without coupling the use case to a database adapter."""
    return analyze_wave(
        buoy_id,
        reader.list_imu(buoy_id, window, None),
        reader.list_locations(buoy_id, window),
        imu_wave_height_factor=imu_wave_height_factor,
    )
