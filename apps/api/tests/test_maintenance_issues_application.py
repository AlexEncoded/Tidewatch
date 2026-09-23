from datetime import datetime, timedelta, timezone

from app.application.maintenance_issues import (
    build_battery_maintenance_issues,
    build_device_maintenance_issues,
    build_maintenance_issues_for_buoy,
    build_operational_maintenance_issues,
    build_sensor_health_maintenance_issues,
)
from app.models import BatteryHealth, DeviceHealth, SensorHealth


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


def test_device_maintenance_service_reports_stale_physical_units() -> None:
    devices = [
        DeviceHealth(
            buoy_id="buoy-1",
            device_id="unit-a",
            sensor_channel="A",
            status="active",
            is_stale=True,
        ),
        DeviceHealth(
            buoy_id="buoy-1",
            device_id="unit-b",
            sensor_channel="B",
            status="active",
            is_stale=False,
        ),
    ]

    issues = build_device_maintenance_issues("buoy-1", "North buoy", devices)

    assert [issue.issue_type for issue in issues] == ["stale_device"]
    assert "unit-a" in issues[0].message


def test_maintenance_issue_service_composes_buoy_snapshot() -> None:
    now = datetime.now(timezone.utc)
    health = SensorHealth(
        buoy_id="buoy-1",
        status="degraded",
        degraded_sensors=["temperature"],
        checked_at=now,
    )
    battery_health = BatteryHealth(
        buoy_id="buoy-1",
        status="healthy",
        device_a_percent=80,
        device_b_percent=80,
        checked_at=now,
    )

    issues = build_maintenance_issues_for_buoy(
        "buoy-1",
        "North buoy",
        "active",
        now,
        now,
        30,
        1,
        health,
        {"temperature": []},
        {"A": None, "B": None},
        battery_health,
        2,
    )

    assert [issue.issue_type for issue in issues] == ["degraded_sensor", "drift_detected"]
