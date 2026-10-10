from datetime import datetime, timedelta, timezone
from math import inf, nan, pi, sin

import pytest

from app.domain.wave import estimate_wave, estimate_wave_period


def test_estimate_wave_requires_two_samples_per_signal() -> None:
    estimate = estimate_wave([2.0], [9.8])

    assert estimate.gnss_vertical_range_m is None
    assert estimate.imu_vertical_acceleration_range_mps2 is None
    assert estimate.estimated_wave_height_m is None
    assert estimate.confidence == "insufficient_data"


def test_estimate_wave_uses_injected_imu_calibration_factor() -> None:
    estimate = estimate_wave([], [9.8, 10.3], imu_wave_height_factor=0.2)

    assert estimate.imu_vertical_acceleration_range_mps2 == 0.5
    assert estimate.estimated_wave_height_m == 0.1
    assert estimate.confidence == "partial"


def test_estimate_wave_ignores_non_finite_sensor_samples() -> None:
    estimate = estimate_wave(
        [2.0, nan, 2.4, inf],
        [9.7, 10.2, nan],
        imu_wave_height_factor=0.2,
    )

    assert estimate.gnss_vertical_range_m == 0.4
    assert estimate.imu_vertical_acceleration_range_mps2 == 0.5
    assert estimate.estimated_wave_height_m == 0.25
    assert estimate.confidence == "experimental"


def test_estimate_wave_uses_default_factor_if_calibration_is_non_finite() -> None:
    estimate = estimate_wave([2.0, 2.4], [9.7, 10.2], imu_wave_height_factor=nan)

    assert estimate.estimated_wave_height_m == 0.225


@pytest.mark.parametrize(
    ("factor", "expected_height"),
    ((-0.2, 0.0), (10.1, 5.0)),
)
def test_estimate_wave_bounds_injected_calibration_factor(
    factor: float, expected_height: float
) -> None:
    estimate = estimate_wave([], [9.8, 10.3], imu_wave_height_factor=factor)

    assert estimate.estimated_wave_height_m == expected_height


def test_estimate_wave_period_ignores_non_finite_values() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    samples = [
        (start + timedelta(seconds=seconds), value)
        for seconds, value in (
            (0, -1.0),
            (10, nan),
            (20, 1.0),
            (30, -1.0),
            (40, inf),
            (50, 1.0),
        )
    ]

    assert estimate_wave_period(samples) == 30.0


def test_estimate_wave_period_removes_linear_gnss_drift() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    samples = [
        (
            start + timedelta(seconds=seconds),
            sin(2 * pi * seconds / 20) + 0.03 * seconds,
        )
        for seconds in range(0, 102, 2)
    ]

    assert estimate_wave_period(samples) == pytest.approx(20.0, abs=0.3)


def test_estimate_wave_period_does_not_bridge_telemetry_gaps() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sample_seconds = [*range(0, 41, 5), *range(3600, 3641, 5)]
    samples = [
        (
            start + timedelta(seconds=seconds),
            sin(2 * pi * seconds / 20),
        )
        for seconds in sample_seconds
    ]
    samples.insert(3, samples[3])  # Duplicate timestamps must not skew the period.

    assert estimate_wave_period(samples) == 20.0


def test_estimate_wave_period_interpolates_mean_crossings() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    samples = [
        (start + timedelta(seconds=seconds), value)
        for seconds, value in ((0, -1.0), (30, 1.0), (60, -1.0), (90, 1.0), (120, -1.0))
    ]

    assert estimate_wave_period(samples) == 60.0


def test_estimate_wave_period_normalizes_naive_timestamps() -> None:
    samples = [
        (datetime(2026, 1, 1, 0, 0, seconds), value)
        for seconds, value in ((0, -1.0), (10, 1.0), (20, -1.0), (30, 1.0))
    ]

    assert estimate_wave_period(samples) == 20.0
