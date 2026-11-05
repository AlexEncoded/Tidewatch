from dataclasses import dataclass
from datetime import datetime, timezone

from .telemetry_types import (
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    FIRMWARE_VERSION_MAX_LENGTH,
    ReadingQuality,
    SENSOR_ID_MAX_LENGTH,
    SensorChannel,
    VALID_READING_QUALITIES,
    VALID_SENSOR_CHANNELS,
)


class SensorTelemetrySnapshot:
    """Runtime invariants shared by snapshots for redundant sensors."""

    sensor_channel: SensorChannel
    quality: ReadingQuality

    def __post_init__(self) -> None:
        if self.sensor_channel not in VALID_SENSOR_CHANNELS:
            raise ValueError(f"Unsupported sensor channel {self.sensor_channel!r}")
        if self.quality not in VALID_READING_QUALITIES:
            raise ValueError(f"Unsupported reading quality {self.quality!r}")
        _validate_device_id(getattr(self, "device_id", None))
        sensor_id = getattr(self, "sensor_id", None)
        if sensor_id is not None and len(sensor_id) > SENSOR_ID_MAX_LENGTH:
            raise ValueError(f"Sensor ID must be at most {SENSOR_ID_MAX_LENGTH} characters")
        firmware_version = getattr(self, "firmware_version", None)
        if firmware_version is not None and len(firmware_version) > FIRMWARE_VERSION_MAX_LENGTH:
            raise ValueError(
                f"Firmware version must be at most {FIRMWARE_VERSION_MAX_LENGTH} characters"
            )


def _validate_device_id(device_id: str | None) -> None:
    if device_id is not None and not DEVICE_ID_MIN_LENGTH <= len(device_id) <= DEVICE_ID_MAX_LENGTH:
        raise ValueError(
            f"Device ID must contain between {DEVICE_ID_MIN_LENGTH} "
            f"and {DEVICE_ID_MAX_LENGTH} characters"
        )


def latest_usable_reading(
    readings: list,
    max_age_seconds: float | None = None,
    now: datetime | None = None,
) -> list:
    """Return the newest valid reading within the optional age window."""
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    for reading in readings:
        if reading.quality == "invalid":
            continue
        if max_age_seconds is not None:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=timezone.utc)
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        return [reading]
    return []
