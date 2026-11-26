from datetime import datetime, timezone

from app.domain.sensors.imu import ImuTelemetrySnapshot
from app.domain.sensors.sensor_health_analysis import calculate_sensor_health_deltas
from app.domain.sensors.temperature import TemperatureTelemetrySnapshot
from app.domain.sensors.wind import WindTelemetrySnapshot
from app.domain.sensors.sensor_health_rules import SENSOR_DEGRADATION_THRESHOLDS


SENSOR_FAMILIES = (
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
)


def _empty_families():
    return {family: {"A": [], "B": []} for family in SENSOR_FAMILIES}


def test_sensor_health_domain_calculates_scalar_and_circular_deltas():
    families = _empty_families()
    families["temperature"] = {
        "A": [TemperatureTelemetrySnapshot("buoy-1", 20.0, datetime.now(timezone.utc))],
        "B": [TemperatureTelemetrySnapshot("buoy-1", 18.5, datetime.now(timezone.utc))],
    }
    families["wind"] = {
        "A": [WindTelemetrySnapshot("buoy-1", 2.0, 359.0, datetime.now(timezone.utc))],
        "B": [WindTelemetrySnapshot("buoy-1", 1.0, 1.0, datetime.now(timezone.utc))],
    }

    deltas = calculate_sensor_health_deltas(families)

    assert deltas["temperature"] == 1.5
    assert deltas["wind_speed"] == 1.0
    assert deltas["wind_direction"] == 2.0


def test_sensor_health_domain_calculates_vector_delta():
    families = _empty_families()
    families["imu"] = {
        "A": [
            ImuTelemetrySnapshot(
                "buoy-1", 1.0, 2.0, 2.0, 0.0, 0.0, 0.0,
                datetime.now(timezone.utc),
            )
        ],
        "B": [
            ImuTelemetrySnapshot(
                "buoy-1", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                datetime.now(timezone.utc),
            )
        ],
    }

    assert calculate_sensor_health_deltas(families)["imu"] == 3.0


def test_each_sensor_health_delta_has_a_degradation_threshold():
    deltas = calculate_sensor_health_deltas(_empty_families())

    assert set(deltas) == set(SENSOR_DEGRADATION_THRESHOLDS)
    assert all(threshold > 0 for threshold in SENSOR_DEGRADATION_THRESHOLDS.values())
