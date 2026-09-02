from collections.abc import Mapping
from dataclasses import dataclass
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
