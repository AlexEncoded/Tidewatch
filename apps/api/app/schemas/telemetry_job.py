"""Public job lifecycle responses; queued payloads are never exposed."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TelemetryJobAcceptedResponse(BaseModel):
    job_id: str
    status: Literal["pending"]
    status_url: str


class TelemetryJobStatusResponse(BaseModel):
    job_id: str
    buoy_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    attempts: int
    available_at: datetime
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
