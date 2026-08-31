"""Application service for the experimental wave-analysis use case."""

from ..analytics import analyze_wave
from ..models import WaveAnalysis
from .ports import ImuTelemetryReader, LocationTelemetryReader


class WaveTelemetryReader(ImuTelemetryReader, LocationTelemetryReader):
    """Input port required by the wave-analysis use case."""


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
