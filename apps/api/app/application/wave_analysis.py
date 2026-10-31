"""Application service for the experimental wave-analysis use case."""

from ..domain.wave import (
    WaveAnalysisSnapshot,
    estimate_fused_wave_period,
    estimate_wave,
    synchronize_wave_readings,
)
from .analysis_ports import WaveAnalysisReader


def analyze_wave_for_buoy(
    reader: WaveAnalysisReader,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
) -> WaveAnalysisSnapshot:
    """Run wave analysis without coupling the use case to a database adapter."""
    imu_readings, locations = synchronize_wave_readings(
        reader.list_imu(buoy_id, window, None),
        reader.list_locations(buoy_id, window),
    )
    estimate = estimate_wave(
        [
            reading.altitude_meters
            for reading in locations
            if reading.altitude_meters is not None
        ],
        [reading.acceleration_z_mps2 for reading in imu_readings],
        imu_wave_height_factor=imu_wave_height_factor,
    )
    gnss_period_samples = [
        (reading.measured_at, reading.altitude_meters)
        for reading in locations
        if reading.altitude_meters is not None
        and getattr(reading, "measured_at", None) is not None
    ]
    imu_period_samples = [
        (reading.measured_at, reading.acceleration_z_mps2)
        for reading in imu_readings
        if getattr(reading, "measured_at", None) is not None
    ]
    period_estimate = estimate_fused_wave_period(
        gnss_period_samples, imu_period_samples
    )
    if estimate.estimated_wave_height_m is None:
        return WaveAnalysisSnapshot(
            buoy_id=buoy_id,
            sample_count=max(len(imu_readings), len(locations)),
            estimated_period_seconds=period_estimate.estimated_period_seconds,
            period_confidence=period_estimate.confidence,
        )
    return WaveAnalysisSnapshot(
        buoy_id=buoy_id,
        sample_count=max(len(imu_readings), len(locations)),
        gnss_vertical_range_m=(
            round(estimate.gnss_vertical_range_m, 3)
            if estimate.gnss_vertical_range_m is not None
            else None
        ),
        imu_vertical_acceleration_range_mps2=(
            round(estimate.imu_vertical_acceleration_range_mps2, 3)
            if estimate.imu_vertical_acceleration_range_mps2 is not None
            else None
        ),
        estimated_wave_height_m=round(estimate.estimated_wave_height_m, 3),
        estimated_period_seconds=period_estimate.estimated_period_seconds,
        period_confidence=period_estimate.confidence,
        confidence=estimate.confidence,
    )
