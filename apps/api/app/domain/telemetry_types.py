"""Shared value types used by telemetry domain objects and API schemas."""

from typing import Literal, get_args

SensorChannel = Literal["A", "B"]
ReadingQuality = Literal["good", "suspect", "invalid"]
VALID_SENSOR_CHANNELS = frozenset(get_args(SensorChannel))
VALID_READING_QUALITIES = frozenset(get_args(ReadingQuality))
WIND_SPEED_MIN_MPS = 0
WIND_SPEED_MAX_MPS = 100
MARINE_CURRENT_SPEED_MIN_MPS = 0
MARINE_CURRENT_SPEED_MAX_MPS = 20
DIRECTION_MIN_DEGREES = 0
DIRECTION_MAX_DEGREES = 360
IMU_ACCELERATION_MIN_MPS2 = -200
IMU_ACCELERATION_MAX_MPS2 = 200
IMU_ANGULAR_VELOCITY_MIN_DPS = -2000
IMU_ANGULAR_VELOCITY_MAX_DPS = 2000
GNSS_ALTITUDE_MIN_METERS = -1000
GNSS_ALTITUDE_MAX_METERS = 20000
GNSS_SPEED_MIN_MPS = 0
GNSS_SPEED_MAX_MPS = 100
GNSS_HDOP_MIN = 0
GNSS_HDOP_MAX = 100
GNSS_SATELLITES_MIN = 0
GNSS_SATELLITES_MAX = 100
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
