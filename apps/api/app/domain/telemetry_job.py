"""Domain contract for durable telemetry-ingestion jobs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

TelemetryJobStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass(frozen=True)
class TelemetryIngestionJobSnapshot:
    """Queue state returned by the persistence adapter."""

    job_id: str
    buoy_id: str
    payload: dict
    status: TelemetryJobStatus
    attempts: int
    available_at: datetime
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    lease_expires_at: datetime | None
    last_error: str | None
