"""Domain contract for durable maintenance notification delivery."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

MaintenanceNotificationStatus = Literal["pending", "processing", "sent", "failed"]


@dataclass(frozen=True)
class MaintenanceNotificationJob:
    job_id: str
    idempotency_key: str
    payload: dict
    issue_count: int
    status: MaintenanceNotificationStatus
    attempts: int
    available_at: datetime
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    lease_expires_at: datetime | None
    last_error: str | None
