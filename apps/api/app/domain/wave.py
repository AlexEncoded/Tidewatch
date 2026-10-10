"""Domain calculations for experimental wave estimation."""

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from statistics import fmean, median
from typing import Sequence


DEFAULT_IMU_WAVE_HEIGHT_FACTOR = 0.1
MIN_IMU_WAVE_HEIGHT_FACTOR = 0.0
MAX_IMU_WAVE_HEIGHT_FACTOR = 10.0


@dataclass(frozen=True)
class WaveEstimate:
    gnss_vertical_range_m: float | None
    imu_vertical_acceleration_range_mps2: float | None
    estimated_wave_height_m: float | None
    confidence: str
    estimated_period_seconds: float | None = None


@dataclass(frozen=True)
class WaveAnalysisSnapshot:
    """Domain result exposed by the experimental wave-analysis use case."""

    buoy_id: str
    sample_count: int
    gnss_vertical_range_m: float | None = None
    imu_vertical_acceleration_range_mps2: float | None = None
    estimated_wave_height_m: float | None = None
    estimated_period_seconds: float | None = None
    confidence: str = "insufficient_data"


def estimate_wave_period(
    samples: Sequence[tuple[datetime, float]],
) -> float | None:
    """Estimate period from upward crossings in contiguous telemetry segments.

    Duplicate timestamps are consolidated. Gaps longer than three nominal
    sample intervals split the record so crossings are never interpolated over
    missing telemetry. Detrending remains conservative to avoid fitting away
    a wave in short records or when the linear trend is weak.
    """
    finite_samples = [
        (timestamp, value)
        for timestamp, value in samples
        if isfinite(value)
    ]
    if len(finite_samples) < 3:
        return None
    timestamp_values: dict[datetime, list[float]] = {}
    for timestamp, value in finite_samples:
        normalized_timestamp = (
            timestamp.replace(tzinfo=timezone.utc)
            if timestamp.tzinfo is None
            else timestamp
        )
        timestamp_values.setdefault(normalized_timestamp, []).append(value)
    normalized_samples = [
        (timestamp, fmean(values))
        for timestamp, values in sorted(timestamp_values.items())
    ]
    if len(normalized_samples) < 3:
        return None

    intervals = [
        (current[0] - previous[0]).total_seconds()
        for previous, current in zip(normalized_samples, normalized_samples[1:])
    ]
    nominal_interval = median(intervals)
    segments: list[list[tuple[datetime, float]]] = [[normalized_samples[0]]]
    for sample, interval in zip(normalized_samples[1:], intervals):
        if interval > nominal_interval * 3:
            segments.append([sample])
        else:
            segments[-1].append(sample)

    periods: list[float] = []
    for segment in segments:
        if len(segment) < 3:
            continue
        origin = segment[0][0]
        elapsed_seconds = [
            (timestamp - origin).total_seconds() for timestamp, _ in segment
        ]
        mean_time = fmean(elapsed_seconds)
        mean_value = fmean(value for _, value in segment)
        time_variance = sum((time - mean_time) ** 2 for time in elapsed_seconds)
        candidate_trend_slope = (
            sum(
                (time - mean_time) * (value - mean_value)
                for time, (_, value) in zip(elapsed_seconds, segment)
            )
            / time_variance
            if time_variance
            else 0.0
        )
        elapsed_span = elapsed_seconds[-1] - elapsed_seconds[0]
        value_range = max(value for _, value in segment) - min(
            value for _, value in segment
        )
        trend_slope = (
            candidate_trend_slope
            if len(segment) >= 8
            and abs(candidate_trend_slope) * elapsed_span > value_range * 0.5
            else 0.0
        )
        detrended_samples = [
            (timestamp, value - (mean_value + trend_slope * (time - mean_time)))
            for time, (timestamp, value) in zip(elapsed_seconds, segment)
        ]
        crossings = []
        for (previous_timestamp, previous_value), (timestamp, value) in zip(
            detrended_samples, detrended_samples[1:]
        ):
            if previous_value >= 0 or value < 0 or value == previous_value:
                continue
            crossing_fraction = -previous_value / (value - previous_value)
            crossings.append(
                previous_timestamp
                + (timestamp - previous_timestamp) * crossing_fraction
            )
        periods.extend(
            (current - previous).total_seconds()
            for previous, current in zip(crossings, crossings[1:])
            if (current - previous).total_seconds() > 0
        )
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
    finite_altitudes = [value for value in gnss_altitudes if isfinite(value)]
    finite_accelerations = [
        value for value in imu_vertical_accelerations if isfinite(value)
    ]
    calibration_factor = (
        max(
            MIN_IMU_WAVE_HEIGHT_FACTOR,
            min(MAX_IMU_WAVE_HEIGHT_FACTOR, imu_wave_height_factor),
        )
        if isfinite(imu_wave_height_factor)
        else DEFAULT_IMU_WAVE_HEIGHT_FACTOR
    )
    gnss_range = (
        max(finite_altitudes) - min(finite_altitudes)
        if len(finite_altitudes) >= 2
        else None
    )
    imu_range = (
        max(finite_accelerations) - min(finite_accelerations)
        if len(finite_accelerations) >= 2
        else None
    )
    imu_wave_height = (
        imu_range * calibration_factor if imu_range is not None else None
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
