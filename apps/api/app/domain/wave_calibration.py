"""Offline evaluation helpers for the experimental GNSS/IMU wave estimate."""

from dataclasses import dataclass
from math import isfinite, sqrt
from statistics import fmean
from typing import Sequence

from .wave import estimate_wave


@dataclass(frozen=True)
class WaveCalibrationWindow:
    """Synchronized sensor samples and an independent reference for one window."""

    gnss_altitudes_m: tuple[float, ...]
    imu_vertical_accelerations_mps2: tuple[float, ...]
    reference_wave_height_m: float


def evaluate_factor(
    windows: Sequence[WaveCalibrationWindow], factor: float
) -> dict[str, float]:
    """Return error metrics for windows that have both sensor modalities."""
    if not windows:
        raise ValueError("At least one calibration window is required")

    errors = []
    for window in windows:
        estimate = estimate_wave(
            window.gnss_altitudes_m,
            window.imu_vertical_accelerations_mps2,
            factor,
        ).estimated_wave_height_m
        if estimate is None:
            raise ValueError("Every window must contain enough GNSS and IMU samples")
        if not isfinite(window.reference_wave_height_m) or window.reference_wave_height_m < 0:
            raise ValueError("Reference wave heights must be finite and non-negative")
        errors.append(estimate - window.reference_wave_height_m)

    return {
        "mae_m": fmean(abs(error) for error in errors),
        "rmse_m": sqrt(fmean(error * error for error in errors)),
        "bias_m": fmean(errors),
    }


def select_factor(
    windows: Sequence[WaveCalibrationWindow], candidates: Sequence[float]
) -> tuple[float, dict[str, float]]:
    """Choose the candidate with minimum calibration RMSE (lower wins ties)."""
    valid_candidates = sorted(
        {
            factor
            for factor in candidates
            if isfinite(factor) and 0 <= factor <= 10
        }
    )
    if not valid_candidates:
        raise ValueError("At least one finite factor between 0 and 10 is required")

    scored = [
        (evaluate_factor(windows, factor)["rmse_m"], factor)
        for factor in valid_candidates
    ]
    _, selected_factor = min(scored)
    return selected_factor, evaluate_factor(windows, selected_factor)
