"""Application service for the experimental wave-analysis use case."""

from collections.abc import Sequence
from datetime import datetime, timezone
from math import isfinite

from ..domain.analytics.wave import (
    DEFAULT_IMU_WAVE_HEIGHT_FACTOR,
    MIN_GNSS_SATELLITES_FOR_WAVE_ANALYSIS,
    WaveAnalysisSnapshot,
    estimate_fused_wave_period,
    estimate_wave,
)
from ..domain.fleet.location import LocationTelemetrySnapshot
from ..domain.sensors.imu import ImuTelemetrySnapshot
from .analysis_ports import WaveAnalysisMetrics, WaveAnalysisReader


def synchronize_wave_readings(
    imu_readings: Sequence[ImuTelemetrySnapshot],
    locations: Sequence[LocationTelemetrySnapshot],
    max_gnss_hdop: float | None = None,
) -> tuple[list[ImuTelemetrySnapshot], list[LocationTelemetrySnapshot]]:
    """Filter unusable readings and align both streams to their shared time span.

    A single available modality remains usable as a partial estimate. When both
    modalities are present, timestamps are required and disjoint ranges yield
    no synchronized readings.
    """
    if max_gnss_hdop is not None and (
        not isfinite(max_gnss_hdop) or max_gnss_hdop <= 0
    ):
        raise ValueError("Maximum GNSS HDOP must be finite and positive")
    usable_imu = [
        reading
        for reading in imu_readings
        if getattr(reading, "quality", "good") == "good"
    ]
    usable_locations = [
        reading
        for reading in locations
        if getattr(reading, "quality", "good") == "good"
        and _gnss_rejection_reason(reading, max_gnss_hdop) is None
    ]
    if not usable_imu or not usable_locations:
        return usable_imu, usable_locations

    timed_imu = [
        (reading, _utc_timestamp(getattr(reading, "measured_at", None)))
        for reading in usable_imu
    ]
    timed_locations = [
        (reading, _utc_timestamp(getattr(reading, "measured_at", None)))
        for reading in usable_locations
    ]
    all_timestamps = [
        timestamp
        for _, timestamp in (*timed_imu, *timed_locations)
    ]
    if any(timestamp is None for timestamp in all_timestamps):
        return [], []

    start_at = max(
        min(timestamp for _, timestamp in timed_imu if timestamp is not None),
        min(timestamp for _, timestamp in timed_locations if timestamp is not None),
    )
    end_at = min(
        max(timestamp for _, timestamp in timed_imu if timestamp is not None),
        max(timestamp for _, timestamp in timed_locations if timestamp is not None),
    )
    if start_at > end_at:
        return [], []

    return (
        [
            reading
            for reading, timestamp in timed_imu
            if timestamp is not None and start_at <= timestamp <= end_at
        ],
        [
            reading
            for reading, timestamp in timed_locations
            if timestamp is not None and start_at <= timestamp <= end_at
        ],
    )


def _gnss_rejection_reason(
    reading: LocationTelemetrySnapshot,
    max_gnss_hdop: float | None,
) -> str | None:
    satellites = getattr(reading, "satellites", None)
    if (
        satellites is not None
        and satellites < MIN_GNSS_SATELLITES_FOR_WAVE_ANALYSIS
    ):
        return "satellite_count"
    hdop = getattr(reading, "hdop", None)
    if max_gnss_hdop is not None and hdop is not None and hdop > max_gnss_hdop:
        return "hdop"
    return None


def _utc_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def analyze_wave_samples(
    buoy_id: str,
    imu_readings: Sequence[ImuTelemetrySnapshot],
    locations: Sequence[LocationTelemetrySnapshot],
    imu_wave_height_factor: float = DEFAULT_IMU_WAVE_HEIGHT_FACTOR,
    max_gnss_hdop: float | None = None,
) -> WaveAnalysisSnapshot:
    """Apply synchronization, height, and period rules to a buoy's samples."""
    rejected_satellite_count = 0
    rejected_hdop_count = 0
    for reading in locations:
        if getattr(reading, "quality", "good") != "good":
            continue
        rejection_reason = _gnss_rejection_reason(reading, max_gnss_hdop)
        if rejection_reason == "satellite_count":
            rejected_satellite_count += 1
        elif rejection_reason == "hdop":
            rejected_hdop_count += 1
    rejected_gnss_sample_count = rejected_satellite_count + rejected_hdop_count
    synchronized_imu, synchronized_locations = synchronize_wave_readings(
        imu_readings, locations, max_gnss_hdop
    )
    estimate = estimate_wave(
        [
            reading.altitude_meters
            for reading in synchronized_locations
            if reading.altitude_meters is not None
        ],
        [reading.acceleration_z_mps2 for reading in synchronized_imu],
        imu_wave_height_factor=imu_wave_height_factor,
    )
    gnss_period_samples = [
        (reading.measured_at, reading.altitude_meters)
        for reading in synchronized_locations
        if reading.altitude_meters is not None
        and getattr(reading, "measured_at", None) is not None
    ]
    imu_period_samples = [
        (reading.measured_at, reading.acceleration_z_mps2)
        for reading in synchronized_imu
        if getattr(reading, "measured_at", None) is not None
    ]
    period_estimate = estimate_fused_wave_period(
        gnss_period_samples, imu_period_samples
    )
    sample_count = max(len(synchronized_imu), len(synchronized_locations))
    if estimate.estimated_wave_height_m is None:
        return WaveAnalysisSnapshot(
            buoy_id=buoy_id,
            sample_count=sample_count,
            rejected_gnss_sample_count=rejected_gnss_sample_count,
            rejected_gnss_satellite_sample_count=rejected_satellite_count,
            rejected_gnss_hdop_sample_count=rejected_hdop_count,
            estimated_period_seconds=period_estimate.estimated_period_seconds,
            period_confidence=period_estimate.confidence,
        )
    return WaveAnalysisSnapshot(
        buoy_id=buoy_id,
        sample_count=sample_count,
        rejected_gnss_sample_count=rejected_gnss_sample_count,
        rejected_gnss_satellite_sample_count=rejected_satellite_count,
        rejected_gnss_hdop_sample_count=rejected_hdop_count,
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


def analyze_wave_for_buoy(
    reader: WaveAnalysisReader,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
    max_gnss_hdop: float | None = None,
) -> WaveAnalysisSnapshot:
    """Compose fleet and sensor samples, then delegate numeric estimates."""
    return analyze_wave_samples(
        buoy_id,
        reader.list_imu(buoy_id, window, None),
        reader.list_locations(buoy_id, window),
        imu_wave_height_factor=imu_wave_height_factor,
        max_gnss_hdop=max_gnss_hdop,
    )


def analyze_and_publish_wave_for_buoy(
    reader: WaveAnalysisReader,
    metrics: WaveAnalysisMetrics,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
    max_gnss_hdop: float | None = None,
) -> WaveAnalysisSnapshot | None:
    """Validate, analyze, and publish one buoy's wave analysis."""
    if not reader.buoy_exists(buoy_id):
        return None
    result = analyze_wave_for_buoy(
        reader, buoy_id, window, imu_wave_height_factor, max_gnss_hdop
    )
    metrics.record_analysis(result)
    return result
