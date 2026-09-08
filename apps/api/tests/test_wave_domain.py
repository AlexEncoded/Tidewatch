from datetime import datetime, timedelta, timezone

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
