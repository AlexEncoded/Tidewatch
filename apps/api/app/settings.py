"""Runtime configuration read by the API composition root and adapters."""

import os
from math import isfinite

from .domain.wave import (
    DEFAULT_IMU_WAVE_HEIGHT_FACTOR,
    MAX_IMU_WAVE_HEIGHT_FACTOR,
    MIN_IMU_WAVE_HEIGHT_FACTOR,
)


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
    if not isfinite(value):
        return DEFAULT_IMU_WAVE_HEIGHT_FACTOR
    return max(MIN_IMU_WAVE_HEIGHT_FACTOR, min(MAX_IMU_WAVE_HEIGHT_FACTOR, value))


def telemetry_ingestion_is_queued() -> bool:
    """Return whether telemetry ingestion is configured to use the queue."""
    return os.getenv("TELEMETRY_INGESTION_MODE", "sync").lower() == "queued"


def configured_maintenance_webhook_url() -> str | None:
    """Return the configured maintenance notification endpoint, if any."""
    value = os.getenv("MAINTENANCE_WEBHOOK_URL")
    return value if value else None


def maintenance_notification_lease_seconds() -> int:
    """Return a valid maintenance-job lease, defaulting to 30 seconds."""
    return _configured_positive_integer(
        "MAINTENANCE_NOTIFICATION_LEASE_SECONDS", default=30, minimum=10
    )


def maintenance_notification_max_attempts() -> int:
    """Return a valid delivery-attempt limit, defaulting to five attempts."""
    return _configured_positive_integer(
        "MAINTENANCE_NOTIFICATION_MAX_ATTEMPTS", default=5, minimum=1
    )


def _configured_positive_integer(name: str, *, default: int, minimum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(minimum, value)


def telemetry_job_lease_seconds() -> int:
    """Return the telemetry-job lease in seconds (default 300, minimum 1)."""
    return _configured_positive_integer(
        "TELEMETRY_JOB_LEASE_SECONDS", default=300, minimum=1
    )


def telemetry_job_max_attempts() -> int:
    """Return the maximum telemetry-job attempts (default 5, minimum 1)."""
    return _configured_positive_integer(
        "TELEMETRY_JOB_MAX_ATTEMPTS", default=5, minimum=1
    )


def telemetry_job_poll_seconds() -> float:
    """Return a finite worker poll interval in seconds (default 2, minimum 0.1)."""
    try:
        value = float(os.getenv("TELEMETRY_JOB_POLL_SECONDS", "2"))
    except ValueError:
        return 2.0
    if not isfinite(value):
        return 2.0
    return max(0.1, value)
