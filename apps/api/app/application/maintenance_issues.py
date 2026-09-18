"""Application services for maintenance issue classification."""

from collections.abc import Mapping, Sequence

from ..domain.reading_quality import classify_latest_readings
from ..domain.maintenance import low_battery_severity, missing_redundant_battery_device
from ..models import BatteryHealth, MaintenanceIssue


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
