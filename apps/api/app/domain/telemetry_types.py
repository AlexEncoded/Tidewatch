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
HUMIDITY_MIN_PERCENT = 0
HUMIDITY_MAX_PERCENT = 100
TURBIDITY_MIN_NTU = 0
TURBIDITY_MAX_NTU = 5000
DISSOLVED_OXYGEN_MIN_MG_L = 0
DISSOLVED_OXYGEN_MAX_MG_L = 20
