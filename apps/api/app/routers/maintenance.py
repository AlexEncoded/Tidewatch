"""HTTP routes for maintenance operations."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from ..application.maintenance_evaluation import evaluate_maintenance_fleet
from ..application.maintenance_notifications import (
    build_maintenance_notification_payload,
    maintenance_notification_idempotency_key,
)
from ..adapter_dependencies import (
    get_maintenance_notification_job_store,
    get_maintenance_reader,
)
from ..application.maintenance_ports import MaintenanceReader
from ..application.maintenance_notification_ports import MaintenanceNotificationJobStore
from ..metrics import (
    battery_delta_percent,
    battery_device_percent,
    buoy_movement_speed_mps,
    redundant_device_missing,
)
from ..schemas.maintenance import (
    MaintenanceIssue,
    MaintenanceNotificationJobStatus,
    MaintenanceNotificationResult,
)
from ..settings import configured_maintenance_webhook_url


router = APIRouter()


def _evaluate_and_publish_maintenance_metrics(
    reader: MaintenanceReader,
    max_age_minutes: float,
    drift_speed_mps: float,
) -> list[MaintenanceIssue]:
    issues: list[MaintenanceIssue] = []
    for buoy, evaluation in evaluate_maintenance_fleet(
        reader, datetime.now(timezone.utc), max_age_minutes, drift_speed_mps
    ):
        for device_id, percentage in (
            ("A", evaluation.battery_health.device_a_percent),
            ("B", evaluation.battery_health.device_b_percent),
        ):
            if percentage is not None:
                battery_device_percent.labels(
                    buoy_id=buoy.buoy_id, device_id=device_id
                ).set(percentage)
        if evaluation.battery_health.delta_percent is not None:
            battery_delta_percent.labels(buoy_id=buoy.buoy_id).set(
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
                buoy_id=buoy.buoy_id, device_id=device_id
            ).set(0 if device_id in available_battery_devices else 1)

        if evaluation.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy.buoy_id).set(
                evaluation.average_speed_mps
            )
        issues.extend(
            MaintenanceIssue.model_validate(issue, from_attributes=True)
            for issue in evaluation.issues
        )
    return issues


@router.get(
    "/api/v1/maintenance/issues",
    response_model=list[MaintenanceIssue],
    tags=["maintenance"],
)
def maintenance_issues(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    reader: MaintenanceReader = Depends(get_maintenance_reader),
) -> list[MaintenanceIssue]:
    return _evaluate_and_publish_maintenance_metrics(
        reader, max_age_minutes, drift_speed_mps
    )


@router.post(
    "/api/v1/maintenance/notifications",
    response_model=MaintenanceNotificationResult,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["maintenance"],
)
def notify_maintenance(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=1, max_length=64
    ),
    reader: MaintenanceReader = Depends(get_maintenance_reader),
    jobs: MaintenanceNotificationJobStore = Depends(
        get_maintenance_notification_job_store
    ),
) -> MaintenanceNotificationResult:
    webhook_url = configured_maintenance_webhook_url()
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MAINTENANCE_WEBHOOK_URL is not configured",
        )

    issues = _evaluate_and_publish_maintenance_metrics(
        reader, max_age_minutes, drift_speed_mps
    )
    payload = build_maintenance_notification_payload(issues)
    requested_at = datetime.now(timezone.utc)
    key = maintenance_notification_idempotency_key(
        payload, idempotency_key, requested_at
    )
    # Receivers can use this stable key to suppress duplicates if a worker
    # crashes after delivery but before it records the successful response.
    payload["notification_idempotency_key"] = key
    try:
        job = jobs.enqueue(key, payload, len(issues), requested_at)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from None
    return MaintenanceNotificationResult(
        job_id=job.job_id,
        status=job.status,
        status_url=f"/api/v1/maintenance/notifications/{job.job_id}",
        issue_count=job.issue_count,
    )


@router.get(
    "/api/v1/maintenance/notifications/{job_id}",
    response_model=MaintenanceNotificationJobStatus,
    tags=["maintenance"],
)
def maintenance_notification_status(
    job_id: str,
    jobs: MaintenanceNotificationJobStore = Depends(
        get_maintenance_notification_job_store
    ),
) -> MaintenanceNotificationJobStatus:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance notification job not found",
        )
    return MaintenanceNotificationJobStatus(
        job_id=job.job_id,
        status=job.status,
        issue_count=job.issue_count,
        attempts=job.attempts,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error=job.last_error,
    )
