"""Application service for sensor-health evaluation."""

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from ..models import SensorHealthCheck
from ..domain.sensor_health import SensorHealthEvaluation, evaluate_sensor_health
from ..domain.telemetry import latest_usable_reading


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


def collect_sensor_readings(
    reader: object,
    buoy_id: str,
    max_age_seconds: float,
    now: datetime,
) -> dict[str, dict[str, object | None]]:
    """Load the latest usable A/B reading for every supported sensor family."""
    sensor_families = (
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
    )
    readings = {}
    for family in sensor_families:
        list_readings = getattr(reader, f"list_{family}")
        readings[family.removesuffix("s")] = {
            channel: latest_usable_reading(
                list_readings(buoy_id, 50, channel), max_age_seconds, now
            )
            for channel in ("A", "B")
        }
    return readings
