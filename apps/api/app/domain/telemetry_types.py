"""Shared value types used by telemetry domain objects and API schemas."""

from typing import Literal, get_args

SensorChannel = Literal["A", "B"]
ReadingQuality = Literal["good", "suspect", "invalid"]
VALID_SENSOR_CHANNELS = frozenset(get_args(SensorChannel))
VALID_READING_QUALITIES = frozenset(get_args(ReadingQuality))
DEVICE_ID_MIN_LENGTH = 1
DEVICE_ID_MAX_LENGTH = 100
SENSOR_ID_MAX_LENGTH = 100
FIRMWARE_VERSION_MAX_LENGTH = 50


def resolve_telemetry_device_id(
    reading_device_id: str | None,
    batch_device_id: str | None,
) -> str | None:
    """Prefer an explicit reading owner, falling back to the batch device."""
    return reading_device_id if reading_device_id is not None else batch_device_id
