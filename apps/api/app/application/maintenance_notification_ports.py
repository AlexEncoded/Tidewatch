"""Input port for durable maintenance notification delivery jobs."""

from datetime import datetime
from typing import Protocol

from ..domain.maintenance_notification_job import MaintenanceNotificationJob


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
