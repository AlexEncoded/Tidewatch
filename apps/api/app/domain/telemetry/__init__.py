"""Telemetry ingestion domain contracts."""

from .family import (
    TELEMETRY_READING_FAMILIES,
    TELEMETRY_RESULT_FAMILIES,
    TelemetryInputFamily,
    TelemetryResultFamily,
)
from .job import (
    TelemetryIngestionJobSnapshot,
    TelemetryJobIdempotencyConflict,
    TelemetryJobStatus,
)
from .job_retry import telemetry_job_retry_delay_seconds
from .quality import QualitySummarySnapshot, summarize_quality_counts

__all__ = [
    "TELEMETRY_READING_FAMILIES",
    "TELEMETRY_RESULT_FAMILIES",
    "TelemetryInputFamily",
    "TelemetryResultFamily",
    "TelemetryIngestionJobSnapshot",
    "TelemetryJobIdempotencyConflict",
    "TelemetryJobStatus",
    "telemetry_job_retry_delay_seconds",
    "QualitySummarySnapshot",
    "summarize_quality_counts",
]
