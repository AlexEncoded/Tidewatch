from dataclasses import fields
from datetime import datetime, timedelta, timezone
from importlib import import_module

from app.application.sensor_health import SENSOR_HEALTH_READING_FAMILIES
from app.domain.maintenance_issues import (
    _SENSOR_READING_DETAILS,
    build_battery_maintenance_issues,
    build_device_maintenance_issues,
    build_maintenance_issues_for_buoy,
    build_operational_maintenance_issues,
    build_sensor_health_maintenance_issues,
)
from app.domain.battery_health import BatteryHealthSnapshot
from app.domain.device_health import DeviceHealthSnapshot
from app.domain.sensor_health_rules import SENSOR_DEGRADATION_THRESHOLDS
from app.domain.temperature import TemperatureTelemetrySnapshot
from app.schemas.sensors import SensorHealth


def test_degraded_sensor_reading_details_cover_every_health_delta() -> None:
    snapshot_types = {
        "temperature": ("temperature", "TemperatureTelemetrySnapshot"),
        "pressure": ("pressure", "PressureTelemetrySnapshot"),
        "salinity": ("salinity", "SalinityTelemetrySnapshot"),
        "imu": ("imu", "ImuTelemetrySnapshot"),
        "ambient_light": ("ambient_light", "AmbientLightTelemetrySnapshot"),
        "wind": ("wind", "WindTelemetrySnapshot"),
        "marine_current": ("marine_current", "MarineCurrentTelemetrySnapshot"),
        "turbidity": ("turbidity", "TurbidityTelemetrySnapshot"),
        "dissolved_oxygen": (
            "dissolved_oxygen",
            "DissolvedOxygenTelemetrySnapshot",
        ),
        "ph": ("ph", "PHTelemetrySnapshot"),
        "conductivity": ("conductivity", "ConductivityTelemetrySnapshot"),
        "chlorophyll_a": ("chlorophyll_a", "ChlorophyllATelemetrySnapshot"),
        "rainfall": ("rainfall", "RainfallTelemetrySnapshot"),
        "humidity": ("humidity", "HumidityTelemetrySnapshot"),
        "air_temperature": ("air_temperature", "AirTemperatureTelemetrySnapshot"),
        "atmospheric_pressure": (
            "atmospheric_pressure",
            "AtmosphericPressureTelemetrySnapshot",
        ),
        "acoustic_altimeter": (
            "acoustic_altimeter",
            "AcousticAltimeterTelemetrySnapshot",
        ),
        "underwater_acoustic": (
            "underwater_acoustic",
            "UnderwaterAcousticTelemetrySnapshot",
        ),
    }
    supported_families = {family for _, family in SENSOR_HEALTH_READING_FAMILIES}

    assert set(_SENSOR_READING_DETAILS) == set(SENSOR_DEGRADATION_THRESHOLDS)
    for sensor, (family, value_attributes, _) in _SENSOR_READING_DETAILS.items():
        assert family in supported_families
        module_name, class_name = snapshot_types[family]
        snapshot_type = getattr(import_module(f"app.domain.{module_name}"), class_name)
        available_fields = {field.name for field in fields(snapshot_type)}
        attributes = (
            value_attributes
            if isinstance(value_attributes, tuple)
            else (value_attributes,)
        )
        assert set(attributes) <= available_fields, sensor


def test_battery_maintenance_service_reports_low_and_missing_units() -> None:
    battery_a = type("Battery", (), {"battery_percent": 8.0})()
    health = BatteryHealthSnapshot(
        buoy_id="buoy-1",
        status="insufficient_data",
        device_a_percent=8.0,
        device_b_percent=None,
        delta_percent=None,
        degraded_devices=(),
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
    checked_at = datetime(2026, 11, 12, tzinfo=timezone.utc)
    health = SensorHealth(
        buoy_id="buoy-1",
        status="degraded",
        degraded_sensors=["temperature"],
        missing_sensors=["pressure:B"],
        temperature_delta_celsius=0.8,
        decisions={"temperature": "fallback_b"},
        checked_at=checked_at,
    )
    last_valid_readings = {
        "temperature": {
            "A": [TemperatureTelemetrySnapshot(
                buoy_id="buoy-1", temperature_celsius=18.5,
                measured_at=checked_at - timedelta(hours=2), sensor_channel="A",
            )],
            "B": [TemperatureTelemetrySnapshot(
                buoy_id="buoy-1", temperature_celsius=19.0,
                measured_at=checked_at - timedelta(minutes=1), sensor_channel="B",
            )],
        }
    }

    issues = build_sensor_health_maintenance_issues(
        "buoy-1", "North buoy", health, last_valid_readings
    )

    assert [issue.issue_type for issue in issues] == [
        "degraded_sensor",
        "missing_sensor_channel",
    ]
    assert (
        "temperature (A/B delta 0.8 °C > tolerance 0.5 °C; selected B;"
        in issues[0].message
    )
    assert "last good: A=18.5 °C at 2026-11-11T22:00:00+00:00" in issues[0].message
    assert "B=19.0 °C at 2026-11-11T23:59:00+00:00" in issues[0].message


def test_degraded_sensor_message_does_not_guess_channel_when_delta_is_ambiguous() -> None:
    health = SensorHealth(
        buoy_id="buoy-1",
        status="degraded",
        degraded_sensors=["temperature"],
        temperature_delta_celsius=1.2,
        decisions={"temperature": "invalid"},
        checked_at=datetime.now(timezone.utc),
    )

    issues = build_sensor_health_maintenance_issues("buoy-1", "North buoy", health)

    assert (
        "temperature (A/B delta 1.2 °C > tolerance 0.5 °C; no channel selected)"
        in issues[0].message
    )


def test_device_maintenance_service_reports_stale_physical_units() -> None:
    devices = [
        DeviceHealthSnapshot(
            buoy_id="buoy-1",
            device_id="unit-a",
            sensor_channel="A",
            status="active",
            is_stale=True,
        ),
        DeviceHealthSnapshot(
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
    battery_health = BatteryHealthSnapshot(
        buoy_id="buoy-1",
        status="consistent",
        device_a_percent=80,
        device_b_percent=80,
        checked_at=now,
        delta_percent=0,
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
