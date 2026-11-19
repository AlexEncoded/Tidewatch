from datetime import datetime, timedelta, timezone
import math

import pytest

from app.domain.wave_direction_experiment import (
    WaveDirectionSample,
    estimate_mean_direction_at_peak_frequency,
    summarize_angular_errors,
)


def _plane_wave_samples(
    direction_towards_degrees: float,
    *,
    count: int = 512,
    interval_seconds: float = 1.0,
    period_seconds: float = 8.0,
) -> list[WaveDirectionSample]:
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    direction = math.radians(direction_towards_degrees)
    samples = []
    for index in range(count):
        elapsed = index * interval_seconds
        elevation = math.cos(2 * math.pi * elapsed / period_seconds)
        horizontal_speed = 0.15 * elevation
        samples.append(
            WaveDirectionSample(
                measured_at=origin + timedelta(seconds=elapsed),
                elevation_m=elevation,
                velocity_east_mps=horizontal_speed * math.sin(direction),
                velocity_north_mps=horizontal_speed * math.cos(direction),
            )
        )
    return samples


@pytest.mark.parametrize("direction", (0, 45, 120, 270, 359))
def test_experimental_mean_direction_recovers_synthetic_compass_bearing(
    direction: float,
) -> None:
    result = estimate_mean_direction_at_peak_frequency(
        _plane_wave_samples(direction),
        minimum_frequency_hz=0.05,
        maximum_frequency_hz=0.4,
        segment_length=128,
    )

    angular_error = abs(result.mean_direction_towards_degrees - direction)
    assert min(angular_error, 360 - angular_error) <= 0.2
    assert result.peak_frequency_hz == pytest.approx(0.125)
    assert result.directional_concentration == pytest.approx(1.0, abs=1e-6)
    assert result.segment_count == 7
    assert result.segment_length == 128


def test_experimental_direction_withholds_result_without_horizontal_energy() -> None:
    samples = [
        WaveDirectionSample(
            measured_at=sample.measured_at,
            elevation_m=sample.elevation_m,
            velocity_east_mps=0,
            velocity_north_mps=0,
        )
        for sample in _plane_wave_samples(90)
    ]

    result = estimate_mean_direction_at_peak_frequency(
        samples,
        minimum_frequency_hz=0.05,
        maximum_frequency_hz=0.4,
        segment_length=128,
    )

    assert result.mean_direction_towards_degrees is None
    assert result.peak_frequency_hz == pytest.approx(0.125)


def test_experimental_direction_withholds_angle_when_first_moment_is_weak() -> None:
    samples = _plane_wave_samples(90)
    samples = [
        WaveDirectionSample(
            measured_at=sample.measured_at,
            elevation_m=sample.elevation_m,
            velocity_east_mps=0.15
            * math.sin(2 * math.pi * index / 8),
            velocity_north_mps=0,
        )
        for index, sample in enumerate(samples)
    ]

    result = estimate_mean_direction_at_peak_frequency(
        samples,
        minimum_frequency_hz=0.05,
        maximum_frequency_hz=0.4,
        segment_length=128,
    )

    assert result.mean_direction_towards_degrees is None
    assert result.directional_concentration < 0.1


def test_experimental_direction_rejects_gaps_and_invalid_frequency_band() -> None:
    samples = _plane_wave_samples(90)
    samples[100] = WaveDirectionSample(
        measured_at=samples[100].measured_at + timedelta(seconds=0.1),
        elevation_m=samples[100].elevation_m,
        velocity_east_mps=samples[100].velocity_east_mps,
        velocity_north_mps=samples[100].velocity_north_mps,
    )
    with pytest.raises(ValueError, match="uniform cadence without gaps"):
        estimate_mean_direction_at_peak_frequency(
            samples,
            minimum_frequency_hz=0.05,
            maximum_frequency_hz=0.4,
            segment_length=128,
        )

    with pytest.raises(ValueError, match="below the Nyquist frequency"):
        estimate_mean_direction_at_peak_frequency(
            _plane_wave_samples(90),
            minimum_frequency_hz=0.05,
            maximum_frequency_hz=0.5,
            segment_length=128,
        )

    with pytest.raises(ValueError, match="no resolvable FFT bins"):
        estimate_mean_direction_at_peak_frequency(
            _plane_wave_samples(90),
            minimum_frequency_hz=0.2,
            maximum_frequency_hz=0.202,
            segment_length=128,
        )


def test_angular_error_summary_uses_circular_bias_across_wraparound() -> None:
    summary = summarize_angular_errors((179, -179))

    assert summary["mean_absolute_error_degrees"] == 179
    assert summary["mean_signed_error_degrees"] == 180


def test_angular_error_summary_withholds_undefined_circular_bias() -> None:
    summary = summarize_angular_errors((90, -90))

    assert summary["mean_absolute_error_degrees"] == 90
    assert summary["mean_signed_error_degrees"] is None
