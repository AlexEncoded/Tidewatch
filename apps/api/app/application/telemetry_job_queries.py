"""Application queries for durable telemetry-ingestion jobs."""

from ..domain.telemetry_job import TelemetryIngestionJobSnapshot
from .telemetry_ports import TelemetryIngestionJobStore


def get_telemetry_job(
    store: TelemetryIngestionJobStore, job_id: str
) -> TelemetryIngestionJobSnapshot | None:
    """Load one telemetry job through its application output port."""
    return store.get(job_id)
