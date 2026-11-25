"""Supported individual sensor families in the telemetry domain."""

from typing import Literal, get_args


SensorFamily = Literal[
    "imu",
    "wind",
    "ambient_light",
    "temperature",
    "pressure",
    "salinity",
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
]
VALID_SENSOR_FAMILIES = frozenset(get_args(SensorFamily))
