"""HTTP routes for maintenance operations."""

from datetime import datetime, timezone
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.battery_health import analyze_battery_health_for_buoy
from ..application.maintenance_notifications import deliver_maintenance_notification
from ..application.movement_analysis import analyze_movement_for_buoy
from ..database import get_db
from ..domain.maintenance import (
    is_buoy_drifting,
    is_buoy_silent,
    low_battery_severity,
    missing_redundant_battery_device,
)
from ..domain.reading_quality import classify_latest_readings
from ..metrics import (
    battery_delta_percent,
    battery_device_percent,
    buoy_movement_speed_mps,
    redundant_device_missing,
)
from ..models import MaintenanceIssue, MaintenanceNotificationResult
from ..repository import BuoyRepository
from .sensors import sensor_health


router = APIRouter()


@router.get(
    "/api/v1/maintenance/issues",
    response_model=list[MaintenanceIssue],
    tags=["maintenance"],
)
def maintenance_issues(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    db: Session = Depends(get_db),
) -> list[MaintenanceIssue]:
    repository = BuoyRepository(db)
    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    issues: list[MaintenanceIssue] = []

    for buoy in repository.list_buoys():
        if is_buoy_silent(buoy.status, buoy.last_seen_at, now, max_age_seconds):
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="silent_buoy",
                    severity="warning",
                    message=f"No telemetry received for more than {max_age_minutes:g} minutes",
                )
            )

        health = sensor_health(buoy.id, max_age_minutes=max_age_minutes, db=db)
        if health.status == "degraded":
            if health.degraded_sensors:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="degraded_sensor",
                        severity="warning",
                        message=f"Degraded sensors: {', '.join(health.degraded_sensors)}",
                    )
                )
            if health.missing_sensors:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="missing_sensor_channel",
                        severity="warning",
                        message=(
                            "No recent telemetry received from sensor channels: "
                            f"{', '.join(health.missing_sensors)}"
                        ),
                    )
                )

        latest_readings = {
            "temperature": repository.list_temperatures(buoy.id, 1),
            "pressure": repository.list_pressures(buoy.id, 1),
            "salinity": repository.list_salinity(buoy.id, 1),
        }
        invalid_sensors, suspect_sensors = classify_latest_readings(latest_readings)
        if invalid_sensors:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="invalid_reading",
                    severity="warning",
                    message=f"Invalid latest readings: {', '.join(invalid_sensors)}",
                )
            )

        if suspect_sensors:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="suspect_reading",
                    severity="warning",
                    message=f"Suspect latest readings: {', '.join(suspect_sensors)}",
                )
            )

        for device_id in ("A", "B"):
            battery = repository.latest_battery(buoy.id, device_id)
            battery_severity = (
                low_battery_severity(battery.battery_percent) if battery is not None else None
            )
            if battery is not None and battery_severity is not None:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="low_battery",
                        severity=battery_severity,
                        message=(
                            f"Battery level for device {device_id} is "
                            f"{battery.battery_percent:.1f}%"
                        ),
                    )
                )

        battery_health_result = analyze_battery_health_for_buoy(repository, buoy.id, 10)
        for device_id, percentage in (
            ("A", battery_health_result.device_a_percent),
            ("B", battery_health_result.device_b_percent),
        ):
            if percentage is not None:
                battery_device_percent.labels(
                    buoy_id=buoy.id, device_id=device_id
                ).set(percentage)
        if battery_health_result.delta_percent is not None:
            battery_delta_percent.labels(buoy_id=buoy.id).set(
                battery_health_result.delta_percent
            )
        available_battery_devices = [
            device_id
            for device_id, percentage in (
                ("A", battery_health_result.device_a_percent),
                ("B", battery_health_result.device_b_percent),
            )
            if percentage is not None
        ]
        for device_id in ("A", "B"):
            redundant_device_missing.labels(
                buoy_id=buoy.id, device_id=device_id
            ).set(0 if device_id in available_battery_devices else 1)
        missing_device = missing_redundant_battery_device(
            battery_health_result.device_a_percent,
            battery_health_result.device_b_percent,
        )
        if missing_device is not None:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="missing_redundant_device",
                    severity="warning",
                    message=(
                        f"No battery telemetry received from redundant device {missing_device}"
                    ),
                )
            )
        if battery_health_result.status == "degraded":
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="degraded_battery",
                    severity="warning",
                    message=(
                        f"Battery units diverge by {battery_health_result.delta_percent:.1f}% "
                        f"(unit {', '.join(battery_health_result.degraded_devices)} suspected)"
                    ),
                )
            )

        movement = analyze_movement_for_buoy(repository, buoy.id, 50)
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy.id).set(movement.average_speed_mps)
        if (
            is_buoy_drifting(movement.average_speed_mps, drift_speed_mps)
        ):
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="drift_detected",
                    severity="warning",
                    message=(
                        f"Average movement speed is {movement.average_speed_mps:.3f} m/s, "
                        f"above the configured limit of {drift_speed_mps:g} m/s"
                    ),
                )
            )

    return issues


@router.post(
    "/api/v1/maintenance/notifications",
    response_model=MaintenanceNotificationResult,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["maintenance"],
)
def notify_maintenance(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    db: Session = Depends(get_db),
) -> MaintenanceNotificationResult:
    webhook_url = os.getenv("MAINTENANCE_WEBHOOK_URL")
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MAINTENANCE_WEBHOOK_URL is not configured",
        )

    issues = maintenance_issues(
        max_age_minutes=max_age_minutes, drift_speed_mps=drift_speed_mps, db=db
    )
    try:
        issue_count = deliver_maintenance_notification(webhook_url, issues, httpx.post)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Maintenance webhook delivery failed",
        ) from exc

    return MaintenanceNotificationResult(status="sent", issue_count=issue_count)
