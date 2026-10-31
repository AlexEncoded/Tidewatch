"""Application service for the experimental wave-analysis use case."""

from ..domain.wave import (
    WaveAnalysisSnapshot,
    analyze_wave_samples,
)
from .analysis_ports import WaveAnalysisReader


def analyze_wave_for_buoy(
    reader: WaveAnalysisReader,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
) -> WaveAnalysisSnapshot:
    """Load sensor samples and delegate analysis to the domain service."""
    return analyze_wave_samples(
        buoy_id,
        reader.list_imu(buoy_id, window, None),
        reader.list_locations(buoy_id, window),
        imu_wave_height_factor=imu_wave_height_factor,
    )
