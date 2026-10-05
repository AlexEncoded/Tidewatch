"""Shared value types used by telemetry domain objects and API schemas."""

from typing import Literal, get_args

SensorChannel = Literal["A", "B"]
ReadingQuality = Literal["good", "suspect", "invalid"]
VALID_SENSOR_CHANNELS = frozenset(get_args(SensorChannel))
VALID_READING_QUALITIES = frozenset(get_args(ReadingQuality))
