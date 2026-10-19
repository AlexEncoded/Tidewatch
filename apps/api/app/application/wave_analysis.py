"""Application service for the experimental wave-analysis use case."""

from datetime import datetime, timezone

from ..domain.wave import (
    WaveAnalysisSnapshot,
    estimate_fused_wave_period,
    estimate_wave,
)
from .ports import WaveAnalysisReader


def analyze_wave_for_buoy(
    reader: WaveAnalysisReader,
    buoy_id: str,
    window: int,
    imu_wave_height_factor: float,
) -> WaveAnalysisSnapshot:
    """Run wave analysis without coupling the use case to a database adapter."""
    imu_readings = [
        reading
        for reading in reader.list_imu(buoy_id, window, None)
        if getattr(reading, "quality", "good") == "good"
    ]
    locations = [
        reading
        for reading in reader.list_locations(buoy_id, window)
        if getattr(reading, "quality", "good") == "good"
    ]
    timed_imu = [
        (reading, _utc_timestamp(getattr(reading, "measured_at", None)))
        for reading in imu_readings
    ]
    timed_locations = [
        (reading, _utc_timestamp(getattr(reading, "measured_at", None)))
        for reading in locations
    ]
    if not timed_imu or not timed_locations:
        # A single available modality can still produce an explicitly partial estimate.
        pass
    elif all(
        timestamp is not None for _, timestamp in (*timed_imu, *timed_locations)
    ):
        start_at = max(
            min(timestamp for _, timestamp in timed_imu if timestamp is not None),
            min(timestamp for _, timestamp in timed_locations if timestamp is not None),
        )
        end_at = min(
            max(timestamp for _, timestamp in timed_imu if timestamp is not None),
            max(timestamp for _, timestamp in timed_locations if timestamp is not None),
        )
        if start_at <= end_at:
            imu_readings = [
                reading
                for reading, timestamp in timed_imu
                if timestamp is not None and start_at <= timestamp <= end_at
            ]
            locations = [
                reading
                for reading, timestamp in timed_locations
                if timestamp is not None and start_at <= timestamp <= end_at
            ]
        else:
            imu_readings = []
            locations = []
    else:
        # Without timestamps there is no safe basis for fusing separate streams.
        imu_readings = []
        locations = []
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
    period = estimate_fused_wave_period(gnss_period_samples, imu_period_samples)
    if estimate.estimated_wave_height_m is None:
        return WaveAnalysisSnapshot(
            buoy_id=buoy_id,
            sample_count=max(len(imu_readings), len(locations)),
            estimated_period_seconds=period,
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
        estimated_period_seconds=period,
        confidence=estimate.confidence,
    )


def _utc_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
