"""Application service for sensor-health evaluation."""

from collections.abc import Mapping

from ..domain.sensor_health import SensorHealthEvaluation, evaluate_sensor_health


def assess_sensor_health(
    deltas: Mapping[str, float | None],
    sensor_readings: Mapping[str, Mapping[str, object | None]],
) -> SensorHealthEvaluation:
    """Evaluate a sensor snapshot through the sensor-health domain rules."""
    return evaluate_sensor_health(deltas, sensor_readings)
