"""Application service for sensor-health evaluation."""

from collections.abc import Mapping
from typing import Protocol

from ..models import SensorHealthCheck
from ..domain.sensor_health import SensorHealthEvaluation, evaluate_sensor_health


class SensorHealthCheckWriter(Protocol):
    """Persistence port required to store a sensor-health evaluation."""

    def add_sensor_health_check(self, health: SensorHealthCheck) -> SensorHealthCheck:
        ...


def assess_sensor_health(
    deltas: Mapping[str, float | None],
    sensor_readings: Mapping[str, Mapping[str, object | None]],
) -> SensorHealthEvaluation:
    """Evaluate a sensor snapshot through the sensor-health domain rules."""
    return evaluate_sensor_health(deltas, sensor_readings)


def persist_sensor_health_check(
    writer: SensorHealthCheckWriter, health: SensorHealthCheck
) -> SensorHealthCheck:
    """Persist a completed sensor-health evaluation through its input port."""
    return writer.add_sensor_health_check(health)
