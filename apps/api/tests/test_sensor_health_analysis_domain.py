from types import SimpleNamespace

from app.domain.sensor_health_analysis import calculate_sensor_health_deltas
from app.domain.sensor_health_rules import SENSOR_DEGRADATION_THRESHOLDS


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
        "A": [SimpleNamespace(temperature_celsius=20.0)],
        "B": [SimpleNamespace(temperature_celsius=18.5)],
    }
    families["wind"] = {
        "A": [SimpleNamespace(wind_speed_mps=2.0, wind_direction_degrees=359.0)],
        "B": [SimpleNamespace(wind_speed_mps=1.0, wind_direction_degrees=1.0)],
    }

    deltas = calculate_sensor_health_deltas(families)

    assert deltas["temperature"] == 1.5
    assert deltas["wind_speed"] == 1.0
    assert deltas["wind_direction"] == 2.0


def test_sensor_health_domain_calculates_vector_delta():
    families = _empty_families()
    families["imu"] = {
        "A": [
            SimpleNamespace(
                acceleration_x_mps2=1.0,
                acceleration_y_mps2=2.0,
                acceleration_z_mps2=2.0,
            )
        ],
        "B": [
            SimpleNamespace(
                acceleration_x_mps2=0.0,
                acceleration_y_mps2=0.0,
                acceleration_z_mps2=0.0,
            )
        ],
    }

    assert calculate_sensor_health_deltas(families)["imu"] == 3.0


def test_each_sensor_health_delta_has_a_degradation_threshold():
    deltas = calculate_sensor_health_deltas(_empty_families())

    assert set(deltas) == set(SENSOR_DEGRADATION_THRESHOLDS)
    assert all(threshold > 0 for threshold in SENSOR_DEGRADATION_THRESHOLDS.values())
