"""Input port for durable maintenance notification delivery jobs."""

from datetime import datetime
from typing import Protocol

from ..domain.maintenance_notification_job import MaintenanceNotificationJob


class MaintenanceNotificationIdempotencyConflict(ValueError):
    """An idempotency key was reused for a different notification payload."""


class MaintenanceNotificationJobStore(Protocol):
    def enqueue(
        self,
        idempotency_key: str,
        payload: dict,
        issue_count: int,
        now: datetime,
    ) -> MaintenanceNotificationJob:
        ...

    def get(self, job_id: str) -> MaintenanceNotificationJob | None:
        ...

    def claim_next(
        self, now: datetime, lease_seconds: int, max_attempts: int
    ) -> MaintenanceNotificationJob | None:
        ...

    def complete(
        self, job_id: str, attempt: int, now: datetime
    ) -> MaintenanceNotificationJob | None:
        ...

    def fail(
        self,
        job_id: str,
        attempt: int,
        error_code: str,
        now: datetime,
        max_attempts: int,
        retry_delay_seconds: int,
    ) -> MaintenanceNotificationJob | None:
        ...
