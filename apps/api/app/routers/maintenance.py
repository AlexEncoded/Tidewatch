"""HTTP routes for maintenance operations."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from ..application.maintenance_evaluation import evaluate_maintenance_issues
from ..application.maintenance_notifications import (
    enqueue_maintenance_notification,
)
from ..adapter_dependencies import (
    get_maintenance_metrics,
    get_maintenance_notification_job_store,
    get_maintenance_reader,
)
from ..application.maintenance_ports import MaintenanceMetrics, MaintenanceReader
from ..application.maintenance_notification_ports import (
    MaintenanceNotificationIdempotencyConflict,
    MaintenanceNotificationJobStore,
)
from ..schemas.maintenance import (
    MaintenanceIssue,
    MaintenanceNotificationJobStatus,
    MaintenanceNotificationResult,
)
from ..settings import configured_maintenance_webhook_url


router = APIRouter()


@router.get(
    "/api/v1/maintenance/issues",
    response_model=list[MaintenanceIssue],
    tags=["maintenance"],
)
def maintenance_issues(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    reader: MaintenanceReader = Depends(get_maintenance_reader),
    metrics: MaintenanceMetrics = Depends(get_maintenance_metrics),
) -> list[MaintenanceIssue]:
    issues = evaluate_maintenance_issues(
        reader, metrics, datetime.now(timezone.utc), max_age_minutes, drift_speed_mps
    )
    return [
        MaintenanceIssue.model_validate(issue, from_attributes=True) for issue in issues
    ]


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
    metrics: MaintenanceMetrics = Depends(get_maintenance_metrics),
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

    issues = evaluate_maintenance_issues(
        reader, metrics, datetime.now(timezone.utc), max_age_minutes, drift_speed_mps
    )
    requested_at = datetime.now(timezone.utc)
    try:
        job = enqueue_maintenance_notification(
            jobs, issues, requested_at, idempotency_key
        )
    except MaintenanceNotificationIdempotencyConflict as exc:
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
