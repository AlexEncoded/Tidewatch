"""Public job lifecycle responses; queued payloads are never exposed."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from ..domain.telemetry_job import TelemetryJobStatus


class TelemetryJobAcceptedResponse(BaseModel):
    job_id: str
    status: TelemetryJobStatus
    status_url: str


class TelemetryJobStatusResponse(BaseModel):
    job_id: str
    buoy_id: str
    status: TelemetryJobStatus
    attempts: int
    available_at: datetime
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error: Literal["processing_failed"] | None
