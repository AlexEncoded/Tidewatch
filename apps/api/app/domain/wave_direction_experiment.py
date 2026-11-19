"""Offline experimental direction estimate from synchronized GNSS eta/u/v samples.

This module is deliberately not used by the API. It implements a first- and
second-order directional-moment estimate for research and synthetic evaluation;
field validation is required before operational use.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean, median


MIN_SEGMENT_LENGTH = 16
MIN_DIRECTIONAL_CONCENTRATION = 0.1
MIN_SPECTRAL_ENERGY = 1e-24


@dataclass(frozen=True)
class WaveDirectionSample:
    """One synchronized surface-elevation and horizontal-velocity sample."""

    measured_at: datetime
    elevation_m: float
    velocity_east_mps: float
    velocity_north_mps: float


@dataclass(frozen=True)
class WaveDirectionEstimate:
    """Mean direction at the elevation peak frequency; never an API response."""

    mean_direction_towards_degrees: float | None
    peak_frequency_hz: float | None
    directional_concentration: float
    sample_count: int
    segment_count: int
    segment_length: int


def estimate_mean_direction_at_peak_frequency(
    samples: Sequence[WaveDirectionSample],
    *,
    minimum_frequency_hz: float,
    maximum_frequency_hz: float,
    segment_length: int | None = None,
) -> WaveDirectionEstimate:
    """Estimate mean direction at peak elevation frequency from eta/u/v spectra.

    The frequency band and segment size must be selected for the deployment's
    sampling protocol. Irregular or incomplete records are rejected instead of
    interpolated. Direction is a compass bearing clockwise from true north,
    describing where the waves travel toward.
    """
    if len(samples) < MIN_SEGMENT_LENGTH * 2:
        raise ValueError("at least 32 synchronized samples are required")
    if not (
        math.isfinite(minimum_frequency_hz)
        and math.isfinite(maximum_frequency_hz)
        and 0 < minimum_frequency_hz < maximum_frequency_hz
    ):
        raise ValueError("frequency band must be finite, positive and increasing")

    timestamps = [_timestamp_seconds(sample.measured_at) for sample in samples]
    intervals = [right - left for left, right in zip(timestamps, timestamps[1:])]
    if any(interval <= 0 for interval in intervals):
        raise ValueError("sample timestamps must be strictly increasing")
    sample_interval = median(intervals)
    if any(
        abs(interval - sample_interval) > max(1e-6, sample_interval * 0.01)
        for interval in intervals
    ):
        raise ValueError("sample timestamps must have a uniform cadence without gaps")

    if maximum_frequency_hz >= 0.5 / sample_interval:
        raise ValueError("maximum frequency must be below the Nyquist frequency")
    if segment_length is None:
        segment_length = 1 << ((len(samples) // 2).bit_length() - 1)
    if (
        segment_length < MIN_SEGMENT_LENGTH
        or segment_length & (segment_length - 1)
        or segment_length > len(samples) // 2
    ):
        raise ValueError(
            "segment length must be a power of two between 16 and half the record"
        )

    signals = [
        [sample.elevation_m for sample in samples],
        [sample.velocity_east_mps for sample in samples],
        [sample.velocity_north_mps for sample in samples],
    ]
    if any(not math.isfinite(value) for signal in signals for value in signal):
        raise ValueError("samples must contain only finite values")

    step = segment_length // 2
    frequency_resolution = 1 / (segment_length * sample_interval)
    if not any(
        minimum_frequency_hz <= index * frequency_resolution <= maximum_frequency_hz
        for index in range(1, segment_length // 2 + 1)
    ):
        raise ValueError("frequency band contains no resolvable FFT bins")
    starts = range(0, len(samples) - segment_length + 1, step)
    window = [
        0.5 - 0.5 * math.cos(2 * math.pi * index / (segment_length - 1))
        for index in range(segment_length)
    ]
    spectra: dict[int, list[tuple[complex, complex, complex]]] = {}
    segment_count = 0
    for start in starts:
        transformed = []
        for signal in signals:
            segment = signal[start : start + segment_length]
            detrended = _remove_linear_trend(segment)
            prepared = [
                value * weight for value, weight in zip(detrended, window)
            ]
            transformed.append(_fft_real(prepared))
        for frequency_index in range(segment_length // 2 + 1):
            spectra.setdefault(frequency_index, []).append(
                tuple(signal[frequency_index] for signal in transformed)
            )
        segment_count += 1

    peak: tuple[float, float, float, float, float, float] | None = None
    for frequency_index, segment_spectra in spectra.items():
        frequency_hz = frequency_index / (segment_length * sample_interval)
        if not minimum_frequency_hz <= frequency_hz <= maximum_frequency_hz:
            continue
        eta_energy = sum(abs(eta) ** 2 for eta, _, _ in segment_spectra)
        east_energy = sum(abs(east) ** 2 for _, east, _ in segment_spectra)
        north_energy = sum(abs(north) ** 2 for _, _, north in segment_spectra)
        east_cross = sum(
            (eta.conjugate() * east).real for eta, east, _ in segment_spectra
        )
        north_cross = sum(
            (eta.conjugate() * north).real for eta, _, north in segment_spectra
        )
        if peak is None or eta_energy > peak[1]:
            peak = (
                frequency_hz,
                eta_energy,
                east_energy,
                north_energy,
                east_cross,
                north_cross,
            )

    if peak is None or peak[1] <= MIN_SPECTRAL_ENERGY:
        return WaveDirectionEstimate(
            None, None, 0.0, len(samples), segment_count, segment_length
        )

    (
        peak_frequency,
        eta_energy,
        east_energy,
        north_energy,
        east_cross,
        north_cross,
    ) = peak
    horizontal_energy = east_energy + north_energy
    denominator = math.sqrt(eta_energy * horizontal_energy)
    if denominator <= MIN_SPECTRAL_ENERGY:
        return WaveDirectionEstimate(
            None, peak_frequency, 0.0, len(samples), segment_count, segment_length
        )

    first_east = east_cross / denominator
    first_north = north_cross / denominator
    concentration = math.hypot(first_east, first_north)
    if concentration < MIN_DIRECTIONAL_CONCENTRATION:
        return WaveDirectionEstimate(
            None,
            peak_frequency,
            concentration,
            len(samples),
            segment_count,
            segment_length,
        )

    # The eta/u/v method uses east as x, north as y, and angles increasing
    # counter-clockwise. Convert that angle to a compass bearing clockwise
    # from north. This prototype reports the first-moment mean at the elevation
    # peak frequency; it does not reconstruct the full directional distribution.
    theta = math.degrees(math.atan2(first_north, first_east))
    direction_towards = (90 - theta) % 360
    return WaveDirectionEstimate(
        round(direction_towards, 1),
        peak_frequency,
        round(concentration, 6),
        len(samples),
        segment_count,
        segment_length,
    )


def summarize_angular_errors(errors_degrees: Sequence[float]) -> dict[str, float | None]:
    """Summarize angular errors without treating the 0/360 boundary linearly."""
    if not errors_degrees:
        return {
            "mean_absolute_error_degrees": None,
            "root_mean_square_error_degrees": None,
            "mean_signed_error_degrees": None,
        }
    if any(not math.isfinite(error) for error in errors_degrees):
        raise ValueError("angular errors must be finite")

    normalized_errors = [(error + 180) % 360 - 180 for error in errors_degrees]
    mean_sine = mean(math.sin(math.radians(error)) for error in normalized_errors)
    mean_cosine = mean(math.cos(math.radians(error)) for error in normalized_errors)
    resultant_length = math.hypot(mean_sine, mean_cosine)
    circular_bias = (
        math.degrees(math.atan2(mean_sine, mean_cosine))
        if resultant_length >= 1e-12
        else None
    )
    return {
        "mean_absolute_error_degrees": round(
            mean(abs(error) for error in normalized_errors), 3
        ),
        "root_mean_square_error_degrees": round(
            math.sqrt(mean(error**2 for error in normalized_errors)), 3
        ),
        "mean_signed_error_degrees": (
            round(circular_bias, 3) if circular_bias is not None else None
        ),
    }


def _timestamp_seconds(value: datetime) -> float:
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.timestamp()


def _fft_real(values: Sequence[float]) -> list[complex]:
    """Return the non-negative bins of a radix-2 FFT for a real-valued series."""
    transformed = [complex(value) for value in values]
    length = len(transformed)
    reversed_index = 0
    for index in range(1, length):
        bit = length >> 1
        while reversed_index & bit:
            reversed_index ^= bit
            bit >>= 1
        reversed_index ^= bit
        if index < reversed_index:
            transformed[index], transformed[reversed_index] = (
                transformed[reversed_index],
                transformed[index],
            )

    block_length = 2
    while block_length <= length:
        half_block = block_length // 2
        angle = -2 * math.pi / block_length
        root = complex(math.cos(angle), math.sin(angle))
        for block_start in range(0, length, block_length):
            twiddle = 1 + 0j
            for offset in range(half_block):
                even = transformed[block_start + offset]
                odd = transformed[block_start + offset + half_block] * twiddle
                transformed[block_start + offset] = even + odd
                transformed[block_start + offset + half_block] = even - odd
                twiddle *= root
        block_length *= 2
    return transformed[: length // 2 + 1]


def _remove_linear_trend(values: Sequence[float]) -> list[float]:
    """Remove each Welch segment's least-squares line before windowing."""
    length = len(values)
    mean_value = mean(values)
    mean_index = (length - 1) / 2
    denominator = sum((index - mean_index) ** 2 for index in range(length))
    slope = sum(
        (index - mean_index) * (value - mean_value)
        for index, value in enumerate(values)
    ) / denominator
    return [
        value - mean_value - slope * (index - mean_index)
        for index, value in enumerate(values)
    ]
