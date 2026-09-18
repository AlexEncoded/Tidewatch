from datetime import datetime, timedelta, timezone

from app.application.maintenance_issues import (
    build_battery_maintenance_issues,
    build_operational_maintenance_issues,
    build_sensor_health_maintenance_issues,
)
from app.models import BatteryHealth, SensorHealth


def test_battery_maintenance_service_reports_low_and_missing_units() -> None:
    battery_a = type("Battery", (), {"battery_percent": 8.0})()
    health = BatteryHealth(
        buoy_id="buoy-1",
        status="healthy",
        device_a_percent=8.0,
        device_b_percent=None,
        delta_percent=None,
        degraded_devices=[],
        checked_at=datetime.now(timezone.utc),
    )

    issues = build_battery_maintenance_issues(
        "buoy-1", "North buoy", {"A": battery_a, "B": None}, health
    )

    assert [issue.issue_type for issue in issues] == [
        "low_battery",
        "missing_redundant_device",
    ]


def test_operational_maintenance_service_reports_silence_and_drift() -> None:
    now = datetime.now(timezone.utc)
    issues = build_operational_maintenance_issues(
        "buoy-1",
        "North buoy",
        "active",
        now - timedelta(minutes=1),
        now,
        max_age_minutes=0.5,
        average_speed_mps=2.0,
        drift_speed_mps=1.0,
    )

    assert [issue.issue_type for issue in issues] == [
        "silent_buoy",
        "drift_detected",
    ]


def test_sensor_health_maintenance_service_reports_degraded_channels() -> None:
    health = SensorHealth(
        buoy_id="buoy-1",
        status="degraded",
        degraded_sensors=["temperature"],
        missing_sensors=["pressure:B"],
        checked_at=datetime.now(timezone.utc),
    )

    issues = build_sensor_health_maintenance_issues(
        "buoy-1", "North buoy", health
    )

    assert [issue.issue_type for issue in issues] == [
        "degraded_sensor",
        "missing_sensor_channel",
    ]
