from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .sensor_completeness import missing_sensor_channels
from .sensor_health_rules import degraded_sensor_names
from .sensor_status import sensor_health_status


ChannelDecision = Literal["average", "fallback_a", "fallback_b", "invalid"]


@dataclass(frozen=True)
class SensorHealthEvaluation:
    status: str
    degraded_sensors: list[str]
    missing_sensors: list[str]
    decisions: dict[str, ChannelDecision]


@dataclass(frozen=True)
class SensorHealthSnapshot:
    """Domain snapshot of redundant sensor health."""

    buoy_id: str
    status: str
    checked_at: datetime
    temperature_delta_celsius: float | None = None
    pressure_delta_kpa: float | None = None
    salinity_delta_psu: float | None = None
    imu_acceleration_delta_mps2: float | None = None
    ambient_light_delta_lux: float | None = None
    wind_speed_delta_mps: float | None = None
    wind_direction_delta_degrees: float | None = None
    marine_current_speed_delta_mps: float | None = None
    marine_current_direction_delta_degrees: float | None = None
    turbidity_delta_ntu: float | None = None
    dissolved_oxygen_delta_mg_l: float | None = None
    ph_delta: float | None = None
    conductivity_delta_us_cm: float | None = None
    chlorophyll_a_delta_ug_l: float | None = None
    rainfall_delta_mm_h: float | None = None
    humidity_delta_percent: float | None = None
    air_temperature_delta_celsius: float | None = None
    atmospheric_pressure_delta_kpa: float | None = None
    acoustic_altimeter_delta_meters: float | None = None
    underwater_acoustic_delta_db: float | None = None
    degraded_sensors: list[str] | None = None
    missing_sensors: list[str] | None = None
    decisions: dict[str, str] | None = None


def decide_channel(
    has_a: bool,
    has_b: bool,
    degraded: bool = False,
) -> ChannelDecision:
    """Choose how the redundant sensor channels should be consumed."""
    if has_a and has_b:
        return "invalid" if degraded else "average"
    if has_a:
        return "fallback_a"
    if has_b:
        return "fallback_b"
    return "invalid"


def evaluate_sensor_health(
    deltas: Mapping[str, float | None],
    sensor_readings: Mapping[str, Mapping[str, object | None]],
) -> SensorHealthEvaluation:
    """Compose redundant-sensor rules into one domain evaluation."""
    missing_sensors = missing_sensor_channels(sensor_readings)
    available = any(value is not None for value in deltas.values())
    degraded_sensors = degraded_sensor_names(deltas)
    decisions = {
        sensor: decide_channel(
            bool(channels["A"]),
            bool(channels["B"]),
            sensor in degraded_sensors,
        )
        for sensor, channels in sensor_readings.items()
    }
    return SensorHealthEvaluation(
        status=sensor_health_status(
            available,
            bool(degraded_sensors),
            bool(missing_sensors),
        ),
        degraded_sensors=degraded_sensors,
        missing_sensors=missing_sensors,
        decisions=decisions,
    )
