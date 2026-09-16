from datetime import datetime, timezone

from app.application.sensor_health import assess_sensor_health
from app.application.sensor_health import persist_sensor_health_check
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
