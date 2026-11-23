"""Durable worker for delivery of maintenance webhooks."""

import logging
from datetime import datetime, timezone

from ..application.maintenance_notifications import (
    MaintenanceNotificationTransport,
    deliver_maintenance_notification_payload,
)
from ..application.maintenance_notification_ports import MaintenanceNotificationJobStore
from ..domain.telemetry_job_retry import telemetry_job_retry_delay_seconds

logger = logging.getLogger(__name__)


def process_next_maintenance_notification_job(
    repository: MaintenanceNotificationJobStore,
    *,
    transport: MaintenanceNotificationTransport,
    lease_seconds: int,
    max_attempts: int,
    webhook_url: str | None = None,
    now: datetime | None = None,
) -> bool:
    """Deliver one job, retrying failures with a durable lease and backoff."""
    claimed_at = now or datetime.now(timezone.utc)
    job = repository.claim_next(claimed_at, lease_seconds, max_attempts)
    if job is None:
        return False

    destination = webhook_url
    try:
        if not destination:
            raise RuntimeError("webhook_not_configured")
        deliver_maintenance_notification_payload(
            destination, job.payload, transport
        )
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
            max_attempts,
            telemetry_job_retry_delay_seconds(job.attempts),
        )
        logger.warning(
            "Maintenance notification job %s failed on attempt %s (state=%s)",
            job.job_id,
            job.attempts,
            failed.status if failed is not None else "lease_lost",
        )
    return True
