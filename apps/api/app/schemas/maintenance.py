"""HTTP contracts for maintenance issues and notification responses."""

from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class MaintenanceIssue(BaseModel):
    buoy_id: str
    buoy_name: str
    issue_type: str
    severity: str
    message: str


class MaintenanceNotificationResult(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "sent", "failed"]
    status_url: str
    issue_count: int


class MaintenanceNotificationJobStatus(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "sent", "failed"]
    issue_count: int
    attempts: int
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
