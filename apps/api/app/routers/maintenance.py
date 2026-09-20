"""HTTP routes for maintenance operations."""

from datetime import datetime, timezone
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.maintenance_evaluation import evaluate_maintenance_buoy
from ..application.maintenance_notifications import deliver_maintenance_notification
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
        evaluation = evaluate_maintenance_buoy(
            repository, buoy, now, max_age_minutes, drift_speed_mps
        )
        for device_id, percentage in (
            ("A", evaluation.battery_health.device_a_percent),
            ("B", evaluation.battery_health.device_b_percent),
        ):
            if percentage is not None:
                battery_device_percent.labels(
                    buoy_id=buoy.id, device_id=device_id
                ).set(percentage)
        if evaluation.battery_health.delta_percent is not None:
            battery_delta_percent.labels(buoy_id=buoy.id).set(
                evaluation.battery_health.delta_percent
            )
        available_battery_devices = [
            device_id
            for device_id, percentage in (
                ("A", evaluation.battery_health.device_a_percent),
                ("B", evaluation.battery_health.device_b_percent),
            )
            if percentage is not None
        ]
        for device_id in ("A", "B"):
            redundant_device_missing.labels(
                buoy_id=buoy.id, device_id=device_id
            ).set(0 if device_id in available_battery_devices else 1)

        if evaluation.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy.id).set(
                evaluation.average_speed_mps
            )
        issues.extend(evaluation.issues)

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
