"""HTTP contracts for maintenance issues and notification responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from ..domain.maintenance import MaintenanceIssueType, MaintenanceSeverity


class MaintenanceIssue(BaseModel):
    buoy_id: str
    buoy_name: str
    issue_type: MaintenanceIssueType
    severity: MaintenanceSeverity
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
