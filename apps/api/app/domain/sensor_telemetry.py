"""Shared invariants for physical sensor telemetry snapshots."""

from .devices import (
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    SENSOR_ID_MAX_LENGTH,
    DEVICE_FIRMWARE_MAX_LENGTH,
    SensorChannel,
    VALID_SENSOR_CHANNELS,
)
from .reading_quality import (
    ReadingQuality,
    VALID_READING_QUALITIES,
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
        if firmware_version is not None and len(firmware_version) > DEVICE_FIRMWARE_MAX_LENGTH:
            raise ValueError(
                f"Firmware version must be at most {DEVICE_FIRMWARE_MAX_LENGTH} characters"
            )


def _validate_device_id(device_id: str | None) -> None:
    if device_id is not None and not DEVICE_ID_MIN_LENGTH <= len(device_id) <= DEVICE_ID_MAX_LENGTH:
        raise ValueError(
            f"Device ID must contain between {DEVICE_ID_MIN_LENGTH} "
            f"and {DEVICE_ID_MAX_LENGTH} characters"
        )
