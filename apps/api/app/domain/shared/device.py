"""Shared physical-device identity constraints and telemetry channels."""

from typing import Literal, get_args

SensorChannel = Literal["A", "B"]
VALID_SENSOR_CHANNELS = frozenset(get_args(SensorChannel))

DEVICE_ID_MIN_LENGTH = 1
DEVICE_ID_MAX_LENGTH = 100
SENSOR_ID_MAX_LENGTH = 100
DEVICE_FIRMWARE_MAX_LENGTH = 50
