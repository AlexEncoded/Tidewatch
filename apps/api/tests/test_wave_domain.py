from datetime import datetime, timedelta, timezone
from math import inf, nan, pi, sin
from types import SimpleNamespace

import pytest

from app.domain.wave import (
    analyze_wave_samples,
    estimate_fused_wave_period,
    estimate_wave,
    estimate_wave_period,
    synchronize_wave_readings,
)


def test_estimate_wave_requires_two_samples_per_signal() -> None:
    estimate = estimate_wave([2.0], [9.8])

    assert estimate.gnss_vertical_range_m is None
    assert estimate.imu_vertical_acceleration_range_mps2 is None
    assert estimate.estimated_wave_height_m is None
    assert estimate.confidence == "insufficient_data"


def test_wave_synchronization_filters_quality_and_keeps_shared_time_window() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    imu = [
        SimpleNamespace(measured_at=start + timedelta(seconds=offset), quality=quality)
        for offset, quality in ((0, "good"), (10, "good"), (20, "good"), (30, "suspect"))
    ]
    locations = [
        SimpleNamespace(
            measured_at=start + timedelta(seconds=offset), quality=quality
        )
        for offset, quality in ((10, "good"), (20, "good"), (30, "good"), (40, "invalid"))
    ]

    synchronized_imu, synchronized_locations = synchronize_wave_readings(imu, locations)

    assert [reading.measured_at for reading in synchronized_imu] == [
        start + timedelta(seconds=10),
        start + timedelta(seconds=20),
    ]
    assert [reading.measured_at for reading in synchronized_locations] == [
        start + timedelta(seconds=10),
        start + timedelta(seconds=20),
    ]


def test_wave_synchronization_rejects_unmatchable_and_disjoint_streams() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    imu = [SimpleNamespace(measured_at=start + timedelta(seconds=offset)) for offset in (0, 1)]
    disjoint_locations = [
        SimpleNamespace(measured_at=start + timedelta(seconds=offset))
        for offset in (2, 3)
    ]
    untimed_locations = [SimpleNamespace()]

    assert synchronize_wave_readings(imu, disjoint_locations) == ([], [])
    assert synchronize_wave_readings(imu, untimed_locations) == ([], [])


def test_wave_synchronization_keeps_single_modality_for_partial_estimation() -> None:
    imu = [SimpleNamespace(quality="good"), SimpleNamespace(quality="suspect")]

    synchronized_imu, locations = synchronize_wave_readings(imu, [])

    assert synchronized_imu == [imu[0]]
    assert locations == []


def test_wave_domain_analysis_builds_snapshot_from_synchronized_samples() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    imu = [
        SimpleNamespace(
            measured_at=start + timedelta(minutes=index),
            acceleration_z_mps2=value,
        )
        for index, value in enumerate((9.7, 10.2))
    ]
    locations = [
        SimpleNamespace(
            measured_at=start + timedelta(minutes=index),
            altitude_meters=value,
        )
        for index, value in enumerate((2.0, 2.4))
    ]

    analysis = analyze_wave_samples("buoy-1", imu, locations)

    assert analysis.buoy_id == "buoy-1"
    assert analysis.sample_count == 2
    assert analysis.gnss_vertical_range_m == 0.4
    assert analysis.imu_vertical_acceleration_range_mps2 == 0.5
    assert analysis.estimated_wave_height_m == 0.225
    assert analysis.confidence == "experimental"


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


def test_fused_wave_period_handles_independent_irregular_sensor_cadences() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def samples(
        step: float, phase: float, amplitude: float
    ) -> list[tuple[datetime, float]]:
        elapsed = phase
        index = 0
        result = []
        while elapsed <= 160:
            result.append(
                (
                    start + timedelta(seconds=elapsed),
                    amplitude * sin(2 * pi * elapsed / 8),
                )
            )
            elapsed += step * (1 + 0.2 * sin(index * 1.7))
            index += 1
        return result

    estimate = estimate_fused_wave_period(
        samples(0.7, 0.0, 1.0),
        samples(1.3, 0.25, 0.5),
    )

    assert estimate.estimated_period_seconds == pytest.approx(8.0, abs=0.02)
    assert estimate.confidence == "experimental"
