"""Supported sensor-family keys accepted in telemetry batches."""

from typing import Literal, get_args


TelemetryInputFamily = Literal[
    "temperatures",
    "pressures",
    "salinity",
    "imu",
    "ambient_light",
    "wind",
    "marine_current",
    "turbidity",
    "dissolved_oxygen",
    "ph",
    "conductivity",
    "chlorophyll_a",
    "rainfall",
    "humidity",
    "air_temperature",
    "atmospheric_pressure",
    "acoustic_altimeter",
    "underwater_acoustic",
    "battery",
]
TelemetryResultFamily = Literal[
    "temperature",
    "pressure",
    "salinity",
    "imu",
    "ambient_light",
    "wind",
    "marine_current",
    "turbidity",
    "dissolved_oxygen",
    "ph",
    "conductivity",
    "chlorophyll_a",
    "rainfall",
    "humidity",
    "air_temperature",
    "atmospheric_pressure",
    "acoustic_altimeter",
    "underwater_acoustic",
    "battery",
]
TELEMETRY_READING_FAMILIES: tuple[TelemetryInputFamily, ...] = get_args(
    TelemetryInputFamily
)
TELEMETRY_RESULT_FAMILIES: tuple[TelemetryResultFamily, ...] = get_args(
    TelemetryResultFamily
)
