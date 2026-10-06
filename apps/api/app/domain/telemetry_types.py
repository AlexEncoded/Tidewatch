"""Shared value types used by telemetry domain objects and API schemas."""

from typing import Literal, get_args

SensorChannel = Literal["A", "B"]
ReadingQuality = Literal["good", "suspect", "invalid"]
VALID_SENSOR_CHANNELS = frozenset(get_args(SensorChannel))
VALID_READING_QUALITIES = frozenset(get_args(ReadingQuality))
AIR_TEMPERATURE_MIN_CELSIUS = -60
AIR_TEMPERATURE_MAX_CELSIUS = 60
ATMOSPHERIC_PRESSURE_MIN_KPA = 80
ATMOSPHERIC_PRESSURE_MAX_KPA = 120
SALINITY_MIN_PSU = 0
SALINITY_MAX_PSU = 45
