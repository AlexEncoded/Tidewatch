"""HTTP contracts for telemetry ingestion."""

from pydantic import BaseModel


class TelemetryIngestResponse(BaseModel):
    buoy_id: str
    accepted_readings: int
    accepted_by_family: dict[str, int]
