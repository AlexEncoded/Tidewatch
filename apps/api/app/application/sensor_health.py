"""Application service for sensor-health evaluation."""

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from ..models import SensorHealthCheck
from ..domain.sensor_health import SensorHealthEvaluation, evaluate_sensor_health
from ..domain.telemetry import latest_usable_reading
from ..domain.deltas import absolute_difference
from ..domain.directions import circular_difference_degrees
from ..domain.vectors import euclidean_difference


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


def calculate_sensor_health_deltas(
    readings: Mapping[str, Mapping[str, list[object]]],
) -> dict[str, float | None]:
    """Calculate redundant-channel deltas from the latest usable readings."""

    def value(family: str, channel: str, attribute: str):
        channel_readings = readings[family][channel]
        return getattr(channel_readings[0], attribute) if channel_readings else None

    def scalar(family: str, attribute: str, digits: int) -> float | None:
        left = value(family, "A", attribute)
        right = value(family, "B", attribute)
        return round(absolute_difference(left, right), digits) if left is not None and right is not None else None

    def circular(family: str, attribute: str, digits: int) -> float | None:
        left = value(family, "A", attribute)
        right = value(family, "B", attribute)
        return round(circular_difference_degrees(left, right), digits) if left is not None and right is not None else None

    imu_a = readings["imu"]["A"]
    imu_b = readings["imu"]["B"]
    imu_delta = (
        round(
            euclidean_difference(
                [getattr(imu_a[0], f"acceleration_{axis}_mps2") for axis in ("x", "y", "z")],
                [getattr(imu_b[0], f"acceleration_{axis}_mps2") for axis in ("x", "y", "z")],
            ),
            3,
        )
        if imu_a and imu_b
        else None
    )
    return {
        "temperature": scalar("temperature", "temperature_celsius", 3),
        "pressure": scalar("pressure", "pressure_kpa", 3),
        "salinity": scalar("salinity", "salinity_psu", 3),
        "imu": imu_delta,
        "ambient_light": scalar("ambient_light", "illuminance_lux", 2),
        "wind_speed": scalar("wind", "wind_speed_mps", 3),
        "wind_direction": circular("wind", "wind_direction_degrees", 2),
        "marine_current_speed": scalar("marine_current", "current_speed_mps", 3),
        "marine_current_direction": circular("marine_current", "current_direction_degrees", 2),
        "turbidity": scalar("turbidity", "turbidity_ntu", 3),
        "dissolved_oxygen": scalar("dissolved_oxygen", "dissolved_oxygen_mg_l", 3),
        "ph": scalar("ph", "ph", 3),
        "conductivity": scalar("conductivity", "conductivity_us_cm", 2),
        "chlorophyll_a": scalar("chlorophyll_a", "chlorophyll_a_ug_l", 3),
        "rainfall": scalar("rainfall", "rainfall_mm_h", 2),
        "humidity": scalar("humidity", "humidity_percent", 2),
        "air_temperature": scalar("air_temperature", "air_temperature_celsius", 2),
        "atmospheric_pressure": scalar("atmospheric_pressure", "atmospheric_pressure_kpa", 3),
        "acoustic_altimeter": scalar("acoustic_altimeter", "depth_meters", 3),
        "underwater_acoustic": scalar("underwater_acoustic", "echo_intensity_db", 2),
    }
