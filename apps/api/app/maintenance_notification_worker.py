"""Durable worker for delivery of maintenance webhooks."""

import logging
import os
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from .application.telemetry_job_retry import telemetry_job_retry_delay_seconds
from .maintenance_notification_job_repository import MaintenanceNotificationJobRepository

logger = logging.getLogger(__name__)
JOB_LEASE_SECONDS = max(10, int(os.getenv("MAINTENANCE_NOTIFICATION_LEASE_SECONDS", "30")))
JOB_MAX_ATTEMPTS = max(1, int(os.getenv("MAINTENANCE_NOTIFICATION_MAX_ATTEMPTS", "5")))


def process_next_maintenance_notification_job(
    db: Session,
    *,
    transport=httpx.post,
    webhook_url: str | None = None,
    now: datetime | None = None,
) -> bool:
    """Deliver one job, retrying failures with a durable lease and backoff."""
    repository = MaintenanceNotificationJobRepository(db)
    claimed_at = now or datetime.now(timezone.utc)
    job = repository.claim_next(claimed_at, JOB_LEASE_SECONDS, JOB_MAX_ATTEMPTS)
    if job is None:
        return False

    destination = webhook_url or os.getenv("MAINTENANCE_WEBHOOK_URL")
    try:
        if not destination:
            raise RuntimeError("webhook_not_configured")
        transport(destination, json=job.payload, timeout=5).raise_for_status()
        completed = repository.complete(
            job.job_id, job.attempts, datetime.now(timezone.utc)
        )
        if completed is None:
            raise RuntimeError("notification_job_lease_expired")
    except Exception as exc:
        error_code = (
            str(exc)
            if isinstance(exc, RuntimeError)
            and str(exc) in {"webhook_not_configured", "notification_job_lease_expired"}
            else "delivery_failed"
        )
        failed = repository.fail(
            job.job_id,
            job.attempts,
            error_code,
            datetime.now(timezone.utc),
            JOB_MAX_ATTEMPTS,
            telemetry_job_retry_delay_seconds(job.attempts),
        )
        logger.warning(
            "Maintenance notification job %s failed on attempt %s (state=%s)",
            job.job_id,
            job.attempts,
            failed.status if failed is not None else "lease_lost",
        )
    return True
