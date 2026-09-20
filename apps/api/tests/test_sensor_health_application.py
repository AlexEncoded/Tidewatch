from datetime import datetime, timezone
from types import SimpleNamespace

from app.application.sensor_health import (
    assess_sensor_health,
    calculate_sensor_health_deltas,
    collect_sensor_readings,
    evaluate_sensor_health_snapshot,
    persist_sensor_health_check,
)
from app.domain.sensor_health_rules import SENSOR_DEGRADATION_THRESHOLDS
from app.models import SensorHealthCheck


def test_sensor_health_application_service_delegates_snapshot_evaluation() -> None:
    evaluation = assess_sensor_health(
        {"temperature": 0.2},
        {"temperature": {"A": object(), "B": object()}},
    )

    assert evaluation.status == "consistent"
    assert evaluation.decisions["temperature"] == "average"


def test_sensor_health_application_service_persists_through_writer_port() -> None:
    health = SensorHealthCheck(
        id=7,
        buoy_id="buoy-1",
        status="consistent",
        checked_at=datetime.now(timezone.utc),
    )

    class Writer:
        def add_sensor_health_check(self, value: SensorHealthCheck) -> SensorHealthCheck:
            assert value is health
            return value

    assert persist_sensor_health_check(Writer(), health) is health


def test_sensor_health_application_service_collects_redundant_channels() -> None:
    class Reader:
        def __getattr__(self, name):
            if name.startswith("list_"):
                return lambda buoy_id, limit, channel: []
            raise AttributeError(name)

    readings = collect_sensor_readings(
        Reader(), "buoy-1", 1800, datetime.now(timezone.utc)
    )

    assert len(readings) == 18
    assert set(readings["temperature"]) == {"A", "B"}
    assert readings["underwater_acoustic"]["A"] == []


def test_sensor_health_application_service_maps_a_complete_snapshot() -> None:
    class Reader:
        def __getattr__(self, name):
            if name.startswith("list_"):
                return lambda buoy_id, limit, channel: []
            raise AttributeError(name)

    snapshot = evaluate_sensor_health_snapshot(
        Reader(), "buoy-1", 1800, datetime.now(timezone.utc)
    )

    assert snapshot.health.buoy_id == "buoy-1"
    assert snapshot.health.status == "insufficient_data"
    assert snapshot.readings["temperature"]["A"] == []


def test_sensor_health_application_service_calculates_scalar_and_circular_deltas() -> None:
    families = {
        family: {"A": [], "B": []}
        for family in (
            "temperature", "pressure", "salinity", "imu", "ambient_light", "wind",
            "marine_current", "turbidity", "dissolved_oxygen", "ph", "conductivity",
            "chlorophyll_a", "rainfall", "humidity", "air_temperature",
            "atmospheric_pressure", "acoustic_altimeter", "underwater_acoustic",
        )
    }
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


def test_every_sensor_health_delta_has_an_explicit_degradation_margin() -> None:
    families = {
        family: {"A": [], "B": []}
        for family in (
            "temperature", "pressure", "salinity", "imu", "ambient_light", "wind",
            "marine_current", "turbidity", "dissolved_oxygen", "ph", "conductivity",
            "chlorophyll_a", "rainfall", "humidity", "air_temperature",
            "atmospheric_pressure", "acoustic_altimeter", "underwater_acoustic",
        )
    }

    deltas = calculate_sensor_health_deltas(families)

    assert set(deltas) == set(SENSOR_DEGRADATION_THRESHOLDS)
    assert all(threshold > 0 for threshold in SENSOR_DEGRADATION_THRESHOLDS.values())
