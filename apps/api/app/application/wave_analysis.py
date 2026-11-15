"""Application service for the experimental wave-analysis use case."""

from ..domain.wave import (
    WaveAnalysisSnapshot,
    analyze_wave_samples,
)
from .analysis_ports import WaveAnalysisMetrics, WaveAnalysisReader


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


def analyze_and_publish_wave_for_buoy(
    reader: WaveAnalysisReader,
    metrics: WaveAnalysisMetrics,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
) -> WaveAnalysisSnapshot | None:
    """Validate, analyze, and publish one buoy's wave analysis."""
    if not reader.buoy_exists(buoy_id):
        return None
    result = analyze_wave_for_buoy(
        reader, buoy_id, window, imu_wave_height_factor
    )
    metrics.record_analysis(result)
    return result
