from datetime import datetime, timezone

import pytest

from app.application.sensor_health import (
    assess_sensor_health,
    collect_sensor_readings,
    evaluate_sensor_health_snapshot,
    persist_sensor_health_check,
)
from app.domain.sensor_health_rules import SENSOR_DEGRADATION_THRESHOLDS
from app.schemas.sensors import SensorHealth, SensorHealthCheck


def test_sensor_health_application_service_delegates_snapshot_evaluation() -> None:
    evaluation = assess_sensor_health(
        {"temperature": 0.2},
        {"temperature": {"A": object(), "B": object()}},
    )

    assert evaluation.status == "consistent"
    assert evaluation.decisions["temperature"] == "average"


def test_sensor_health_application_service_persists_through_writer_port() -> None:
    health = SensorHealth(
        buoy_id="buoy-1",
        status="consistent",
        checked_at=datetime.now(timezone.utc),
    )
    stored = SensorHealthCheck(id=7, **health.model_dump())

    class Writer:
        def add_sensor_health_check(self, value: SensorHealth) -> SensorHealthCheck:
            assert value is health
            return stored

    assert persist_sensor_health_check(Writer(), health) is stored


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


def test_sensor_health_degradation_margins_are_immutable() -> None:
    with pytest.raises(TypeError):
        SENSOR_DEGRADATION_THRESHOLDS["temperature"] = 1.0
