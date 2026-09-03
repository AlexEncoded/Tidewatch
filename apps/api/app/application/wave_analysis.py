"""Application service for the experimental wave-analysis use case."""

from ..domain.wave import estimate_wave, estimate_wave_period
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
    imu_readings = [
        reading
        for reading in reader.list_imu(buoy_id, window, None)
        if getattr(reading, "quality", "good") != "invalid"
    ]
    locations = [
        reading
        for reading in reader.list_locations(buoy_id, window)
        if getattr(reading, "quality", "good") != "invalid"
    ]
    estimate = estimate_wave(
        [
            reading.altitude_meters
            for reading in locations
            if reading.altitude_meters is not None
        ],
        [reading.acceleration_z_mps2 for reading in imu_readings],
        imu_wave_height_factor=imu_wave_height_factor,
    )
    period_samples = [
        (reading.measured_at, reading.altitude_meters)
        for reading in reversed(locations)
        if reading.altitude_meters is not None
        and getattr(reading, "measured_at", None) is not None
    ]
    period = estimate_wave_period(period_samples)
    if estimate.estimated_wave_height_m is None:
        return WaveAnalysis(
            buoy_id=buoy_id,
            sample_count=max(len(imu_readings), len(locations)),
            estimated_period_seconds=period,
        )
    return WaveAnalysis(
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
        estimated_period_seconds=period,
        confidence=estimate.confidence,
    )
