"""Application service for sensor-health evaluation."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from ..domain.sensor_health import (
    SensorHealthEvaluation,
    SensorHealthCheckSnapshot,
    SensorHealthSnapshot as DomainSensorHealthSnapshot,
    evaluate_sensor_health,
)
from ..domain.devices import SensorChannel
from ..domain.reading_quality import latest_usable_reading
from ..domain.sensor_family import SensorFamily
from ..domain.sensor_health_analysis import calculate_sensor_health_deltas
from ..domain.sensor_health_rules import SensorHealthDeltaName
from ..domain.sensor_telemetry import SensorTelemetrySnapshot
from ..domain.telemetry_family import TelemetryInputFamily
from .sensor_health_ports import SensorHealthCheckWriter, SensorHealthReader


SENSOR_HEALTH_READING_FAMILIES: tuple[
    tuple[TelemetryInputFamily, SensorFamily], ...
] = (
    ("temperatures", "temperature"),
    ("pressures", "pressure"),
    ("salinity", "salinity"),
    ("imu", "imu"),
    ("ambient_light", "ambient_light"),
    ("wind", "wind"),
    ("marine_current", "marine_current"),
    ("turbidity", "turbidity"),
    ("dissolved_oxygen", "dissolved_oxygen"),
    ("ph", "ph"),
    ("conductivity", "conductivity"),
    ("chlorophyll_a", "chlorophyll_a"),
    ("rainfall", "rainfall"),
    ("humidity", "humidity"),
    ("air_temperature", "air_temperature"),
    ("atmospheric_pressure", "atmospheric_pressure"),
    ("acoustic_altimeter", "acoustic_altimeter"),
    ("underwater_acoustic", "underwater_acoustic"),
)
SensorHealthReadings = dict[
    SensorFamily, dict[SensorChannel, list[SensorTelemetrySnapshot]]
]


@dataclass(frozen=True)
class SensorHealthSnapshot:
    """Application result shared by the HTTP and maintenance adapters."""

    readings: SensorHealthReadings
    deltas: dict[SensorHealthDeltaName, float | None]
    evaluation: SensorHealthEvaluation
    health: DomainSensorHealthSnapshot


def assess_sensor_health(
    deltas: Mapping[SensorHealthDeltaName, float | None],
    sensor_readings: Mapping[SensorFamily, Mapping[SensorChannel, object | None]],
) -> SensorHealthEvaluation:
    """Evaluate a sensor snapshot through the sensor-health domain rules."""
    return evaluate_sensor_health(deltas, sensor_readings)


def evaluate_sensor_health_snapshot(
    reader: SensorHealthReader,
    buoy_id: str,
    max_age_seconds: float,
    now: datetime,
) -> SensorHealthSnapshot:
    """Collect, compare and map a buoy's redundant sensor readings."""
    readings = collect_sensor_readings(reader, buoy_id, max_age_seconds, now)
    deltas = calculate_sensor_health_deltas(readings)
    evaluation = assess_sensor_health(deltas, readings)
    health = DomainSensorHealthSnapshot(
        buoy_id=buoy_id,
        status=evaluation.status,
        temperature_delta_celsius=deltas["temperature"],
        pressure_delta_kpa=deltas["pressure"],
        salinity_delta_psu=deltas["salinity"],
        imu_acceleration_delta_mps2=deltas["imu"],
        ambient_light_delta_lux=deltas["ambient_light"],
        wind_speed_delta_mps=deltas["wind_speed"],
        wind_direction_delta_degrees=deltas["wind_direction"],
        marine_current_speed_delta_mps=deltas["marine_current_speed"],
        marine_current_direction_delta_degrees=deltas["marine_current_direction"],
        turbidity_delta_ntu=deltas["turbidity"],
        dissolved_oxygen_delta_mg_l=deltas["dissolved_oxygen"],
        ph_delta=deltas["ph"],
        conductivity_delta_us_cm=deltas["conductivity"],
        chlorophyll_a_delta_ug_l=deltas["chlorophyll_a"],
        rainfall_delta_mm_h=deltas["rainfall"],
        humidity_delta_percent=deltas["humidity"],
        air_temperature_delta_celsius=deltas["air_temperature"],
        atmospheric_pressure_delta_kpa=deltas["atmospheric_pressure"],
        acoustic_altimeter_delta_meters=deltas["acoustic_altimeter"],
        underwater_acoustic_delta_db=deltas["underwater_acoustic"],
        degraded_sensors=evaluation.degraded_sensors,
        missing_sensors=evaluation.missing_sensors,
        decisions=evaluation.decisions,
        checked_at=now,
    )
    return SensorHealthSnapshot(readings, deltas, evaluation, health)


def persist_sensor_health_check(
    writer: SensorHealthCheckWriter, health: DomainSensorHealthSnapshot
) -> SensorHealthCheckSnapshot:
    """Persist a completed sensor-health evaluation through its input port."""
    return writer.add_sensor_health_check(health)


def collect_sensor_readings(
    reader: SensorHealthReader,
    buoy_id: str,
    max_age_seconds: float,
    now: datetime,
) -> SensorHealthReadings:
    """Load the latest usable A/B reading for every supported sensor family."""
    readings: SensorHealthReadings = {}
    channels: tuple[SensorChannel, ...] = ("A", "B")
    for batch_family, sensor_family in SENSOR_HEALTH_READING_FAMILIES:
        list_readings = getattr(reader, f"list_{batch_family}")
        readings[sensor_family] = {
            channel: latest_usable_reading(
                list_readings(buoy_id, 50, channel), max_age_seconds, now
            )
            for channel in channels
        }
    return readings
