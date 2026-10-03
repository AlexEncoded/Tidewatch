"""HTTP contracts for maintenance issues and notification responses."""

from pydantic import BaseModel


class MaintenanceIssue(BaseModel):
    buoy_id: str
    buoy_name: str
    issue_type: str
    severity: str
    message: str


class MaintenanceNotificationResult(BaseModel):
    status: str
    issue_count: int
