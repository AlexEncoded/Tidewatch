from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.application.sensor_health import (
    assess_sensor_health,
    collect_sensor_readings,
    evaluate_and_persist_sensor_health_check,
    evaluate_and_publish_sensor_health,
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


def test_sensor_health_check_orchestrates_buoy_validation_evaluation_metrics_and_write() -> None:
    now = datetime(2026, 11, 12, tzinfo=timezone.utc)
    events = []

    class Gateway:
        def buoy_exists(self, buoy_id):
            events.append(("buoy_exists", buoy_id))
            return True

        def __getattr__(self, name):
            if name.startswith("list_"):
                return lambda buoy_id, limit, channel: []
            if name == "add_sensor_health_check":
                def add(health):
                    events.append(("add_sensor_health_check", health))
                    return SimpleNamespace(id=23, **health.__dict__)

                return add
            raise AttributeError(name)

    class Metrics:
        def record_evaluation(self, *args):
            events.append(("record_evaluation", *args))

    stored = evaluate_and_persist_sensor_health_check(
        Gateway(), Metrics(), "buoy-1", 1800, now
    )

    assert stored.id == 23
    assert stored.buoy_id == "buoy-1"
    assert stored.checked_at == now
    assert [event[0] for event in events].count("record_evaluation") == 1
    assert [event[0] for event in events].count("add_sensor_health_check") == 1
    assert events.index(next(event for event in events if event[0] == "record_evaluation")) < events.index(
        next(event for event in events if event[0] == "add_sensor_health_check")
    )


def test_sensor_health_check_stops_when_buoy_is_unknown() -> None:
    class Gateway:
        def buoy_exists(self, buoy_id):
            return False

        def __getattr__(self, name):
            raise AssertionError(f"unexpected gateway call: {name}")

    class Metrics:
        def record_evaluation(self, *args):
            raise AssertionError("unknown buoy must not publish evaluation metrics")

    assert (
        evaluate_and_persist_sensor_health_check(
            Gateway(), Metrics(), "missing", 1800, datetime.now(timezone.utc)
        )
        is None
    )


def test_sensor_health_read_use_case_validates_buoy_and_publishes_metrics() -> None:
    now = datetime(2026, 11, 12, tzinfo=timezone.utc)

    class Reader:
        def buoy_exists(self, buoy_id):
            assert buoy_id == "buoy-1"
            return True

        def __getattr__(self, name):
            if name.startswith("list_"):
                return lambda buoy_id, limit, channel: []
            raise AttributeError(name)

    class Metrics:
        def __init__(self):
            self.values = []

        def record_evaluation(self, *args):
            self.values.append(args)

    metrics = Metrics()
    snapshot = evaluate_and_publish_sensor_health(
        Reader(), metrics, "buoy-1", 1800, now
    )

    assert snapshot is not None
    assert snapshot.health.buoy_id == "buoy-1"
    assert snapshot.health.checked_at == now
    assert len(metrics.values) == 1


def test_sensor_health_degradation_margins_are_immutable() -> None:
    with pytest.raises(TypeError):
        SENSOR_DEGRADATION_THRESHOLDS["temperature"] = 1.0
