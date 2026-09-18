"""Application services for maintenance issue classification."""

from collections.abc import Mapping, Sequence
from datetime import datetime

from ..domain.maintenance import is_buoy_drifting, is_buoy_silent
from ..domain.reading_quality import classify_latest_readings
from ..domain.maintenance import low_battery_severity, missing_redundant_battery_device
from ..models import BatteryHealth, MaintenanceIssue, SensorHealth


def build_reading_quality_issues(
    buoy_id: str,
    buoy_name: str,
    latest_readings: Mapping[str, Sequence[object]],
) -> list[MaintenanceIssue]:
    """Build maintenance issues for invalid or suspect latest readings."""
    invalid_sensors, suspect_sensors = classify_latest_readings(latest_readings)
    issues: list[MaintenanceIssue] = []

    if invalid_sensors:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="invalid_reading",
                severity="warning",
                message=f"Invalid latest readings: {', '.join(invalid_sensors)}",
            )
        )

    if suspect_sensors:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="suspect_reading",
                severity="warning",
                message=f"Suspect latest readings: {', '.join(suspect_sensors)}",
            )
        )

    return issues


def build_battery_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    latest_batteries: Mapping[str, object | None],
    health: BatteryHealth,
) -> list[MaintenanceIssue]:
    """Build maintenance issues from redundant battery readings and health."""
    issues: list[MaintenanceIssue] = []
    for device_id in ("A", "B"):
        battery = latest_batteries.get(device_id)
        battery_percent = getattr(battery, "battery_percent", None)
        severity = (
            low_battery_severity(battery_percent)
            if battery_percent is not None
            else None
        )
        if severity is not None:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy_id,
                    buoy_name=buoy_name,
                    issue_type="low_battery",
                    severity=severity,
                    message=(
                        f"Battery level for device {device_id} is "
                        f"{battery_percent:.1f}%"
                    ),
                )
            )

    missing_device = missing_redundant_battery_device(
        health.device_a_percent, health.device_b_percent
    )
    if missing_device is not None:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="missing_redundant_device",
                severity="warning",
                message=(
                    f"No battery telemetry received from redundant device {missing_device}"
                ),
            )
        )

    if health.status == "degraded":
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="degraded_battery",
                severity="warning",
                message=(
                    f"Battery units diverge by {health.delta_percent:.1f}% "
                    f"(unit {', '.join(health.degraded_devices)} suspected)"
                ),
            )
        )

    return issues


def build_operational_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    status: str,
    last_seen_at: datetime | None,
    now: datetime,
    max_age_minutes: float,
    average_speed_mps: float | None,
    drift_speed_mps: float,
) -> list[MaintenanceIssue]:
    """Build maintenance issues for silence and unexpected buoy movement."""
    issues: list[MaintenanceIssue] = []
    if is_buoy_silent(status, last_seen_at, now, max_age_minutes * 60):
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="silent_buoy",
                severity="warning",
                message=(
                    f"No telemetry received for more than {max_age_minutes:g} minutes"
                ),
            )
        )

    if is_buoy_drifting(average_speed_mps, drift_speed_mps):
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="drift_detected",
                severity="warning",
                message=(
                    f"Average movement speed is {average_speed_mps:.3f} m/s, "
                    f"above the configured limit of {drift_speed_mps:g} m/s"
                ),
            )
        )

    return issues


def build_sensor_health_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    health: SensorHealth,
) -> list[MaintenanceIssue]:
    """Build maintenance issues for degraded or missing sensor channels."""
    if health.status != "degraded":
        return []

    issues: list[MaintenanceIssue] = []
    if health.degraded_sensors:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="degraded_sensor",
                severity="warning",
                message=f"Degraded sensors: {', '.join(health.degraded_sensors)}",
            )
        )
    if health.missing_sensors:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="missing_sensor_channel",
                severity="warning",
                message=(
                    "No recent telemetry received from sensor channels: "
                    f"{', '.join(health.missing_sensors)}"
                ),
            )
        )
    return issues
