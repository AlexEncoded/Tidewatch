"""HTTP routes for maintenance operations."""

from datetime import datetime, timezone
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.battery_health import analyze_battery_health_for_buoy
from ..application.maintenance_issues import (
    build_battery_maintenance_issues,
    build_operational_maintenance_issues,
    build_reading_quality_issues,
    build_sensor_health_maintenance_issues,
)
from ..application.maintenance_notifications import deliver_maintenance_notification
from ..application.movement_analysis import analyze_movement_for_buoy
from ..application.sensor_health import evaluate_sensor_health_snapshot
from ..database import get_db
from ..metrics import (
    battery_delta_percent,
    battery_device_percent,
    buoy_movement_speed_mps,
    redundant_device_missing,
)
from ..models import MaintenanceIssue, MaintenanceNotificationResult
from ..repository import BuoyRepository


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
    issues: list[MaintenanceIssue] = []

    for buoy in repository.list_buoys():
        health = evaluate_sensor_health_snapshot(
            repository, buoy.id, max_age_minutes * 60, now
        ).health
        issues.extend(
            build_sensor_health_maintenance_issues(buoy.id, buoy.name, health)
        )

        latest_readings = {
            "temperature": repository.list_temperatures(buoy.id, 1),
            "pressure": repository.list_pressures(buoy.id, 1),
            "salinity": repository.list_salinity(buoy.id, 1),
        }
        issues.extend(
            build_reading_quality_issues(buoy.id, buoy.name, latest_readings)
        )

        battery_health_result = analyze_battery_health_for_buoy(repository, buoy.id, 10)
        latest_batteries = {
            device_id: repository.latest_battery(buoy.id, device_id)
            for device_id in ("A", "B")
        }
        issues.extend(
            build_battery_maintenance_issues(
                buoy.id, buoy.name, latest_batteries, battery_health_result
            )
        )
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

        movement = analyze_movement_for_buoy(repository, buoy.id, 50)
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy.id).set(movement.average_speed_mps)
        issues.extend(
            build_operational_maintenance_issues(
                buoy.id,
                buoy.name,
                buoy.status,
                buoy.last_seen_at,
                now,
                max_age_minutes,
                movement.average_speed_mps,
                drift_speed_mps,
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
