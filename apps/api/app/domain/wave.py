"""Domain calculations for experimental wave estimation."""

from dataclasses import dataclass
from statistics import fmean
from typing import Sequence


@dataclass(frozen=True)
class WaveEstimate:
    gnss_vertical_range_m: float | None
    imu_vertical_acceleration_range_mps2: float | None
    estimated_wave_height_m: float | None
    confidence: str


def estimate_wave(
    gnss_altitudes: Sequence[float],
    imu_vertical_accelerations: Sequence[float],
) -> WaveEstimate:
    """Estimate wave height from vertical GNSS and IMU samples.

    This is deliberately an experimental transfer model. The IMU contribution
    uses a conservative synthetic factor until buoy-specific calibration data
    is available.
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
    imu_wave_height = imu_range * 0.1 if imu_range is not None else None
    estimates = [value for value in (gnss_range, imu_wave_height) if value is not None]
    return WaveEstimate(
        gnss_vertical_range_m=gnss_range,
        imu_vertical_acceleration_range_mps2=imu_range,
        estimated_wave_height_m=fmean(estimates) if estimates else None,
        confidence=("experimental" if len(estimates) == 2 else "partial")
        if estimates
        else "insufficient_data",
    )
