"""Domain calculations for experimental wave estimation."""

from dataclasses import dataclass
from datetime import datetime
from statistics import fmean
from typing import Sequence


DEFAULT_IMU_WAVE_HEIGHT_FACTOR = 0.1


@dataclass(frozen=True)
class WaveEstimate:
    gnss_vertical_range_m: float | None
    imu_vertical_acceleration_range_mps2: float | None
    estimated_wave_height_m: float | None
    confidence: str
    estimated_period_seconds: float | None = None


def estimate_wave_period(
    samples: Sequence[tuple[datetime, float]],
) -> float | None:
    """Estimate wave period from consecutive upward mean crossings."""
    if len(samples) < 3:
        return None
    mean = fmean(value for _, value in samples)
    crossings = [
        timestamp
        for (_, previous_value), (timestamp, value) in zip(samples, samples[1:])
        if previous_value < mean <= value
    ]
    if len(crossings) < 2:
        return None
    periods = [
        (current - previous).total_seconds()
        for previous, current in zip(crossings, crossings[1:])
        if (current - previous).total_seconds() > 0
    ]
    return round(fmean(periods), 3) if periods else None


def estimate_wave(
    gnss_altitudes: Sequence[float],
    imu_vertical_accelerations: Sequence[float],
    imu_wave_height_factor: float = DEFAULT_IMU_WAVE_HEIGHT_FACTOR,
) -> WaveEstimate:
    """Estimate wave height from vertical GNSS and IMU samples.

    This is deliberately an experimental transfer model. The IMU contribution
    uses a conservative synthetic factor until buoy-specific calibration data
    is available. ``imu_wave_height_factor`` is injectable so calibration can
    be performed without changing the domain service contract.
    """
    gnss_range = (
        max(gnss_altitudes) - min(gnss_altitudes)
        if len(gnss_altitudes) >= 2
        else None
    )
    imu_range = (
        max(imu_vertical_accelerations) - min(imu_vertical_accelerations)
        if len(imu_vertical_accelerations) >= 2
        else None
    )
    imu_wave_height = (
        imu_range * imu_wave_height_factor if imu_range is not None else None
    )
    estimates = [value for value in (gnss_range, imu_wave_height) if value is not None]
    return WaveEstimate(
        gnss_vertical_range_m=round(gnss_range, 6) if gnss_range is not None else None,
        imu_vertical_acceleration_range_mps2=round(imu_range, 6) if imu_range is not None else None,
        estimated_wave_height_m=round(fmean(estimates), 6) if estimates else None,
        confidence=("experimental" if len(estimates) == 2 else "partial")
        if estimates
        else "insufficient_data",
    )
