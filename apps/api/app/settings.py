"""Runtime configuration read by the API composition root and adapters."""

import os

from .domain.wave import DEFAULT_IMU_WAVE_HEIGHT_FACTOR


def configured_wave_imu_factor() -> float:
    """Return the bounded experimental IMU calibration factor."""
    try:
        value = float(
            os.getenv(
                "WAVE_IMU_WAVE_HEIGHT_FACTOR",
                str(DEFAULT_IMU_WAVE_HEIGHT_FACTOR),
            )
        )
    except ValueError:
        return DEFAULT_IMU_WAVE_HEIGHT_FACTOR
    return max(0.0, min(10.0, value))
