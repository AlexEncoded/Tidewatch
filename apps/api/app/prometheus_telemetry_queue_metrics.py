"""Prometheus adapter for durable telemetry queue metrics."""

from .application.telemetry_ports import TelemetryQueueMetricsPublisher
from .metrics import (
    telemetry_ingestion_attempts,
    telemetry_ingestion_expired_leases,
    telemetry_ingestion_jobs,
    telemetry_ingestion_metrics_collection_success,
    telemetry_ingestion_oldest_pending_seconds,
    telemetry_ingestion_retried_jobs,
)


class PrometheusTelemetryQueueMetrics(TelemetryQueueMetricsPublisher):
    """Publish the bounded queue snapshot through Prometheus instruments."""

    def publish_snapshot(self, snapshot: dict[str, int | float]) -> None:
        for job_status in ("pending", "processing", "completed", "failed"):
            telemetry_ingestion_jobs.labels(status=job_status).set(snapshot[job_status])
            telemetry_ingestion_attempts.labels(status=job_status).set(
                snapshot[f"{job_status}_attempts"]
            )
        telemetry_ingestion_retried_jobs.set(snapshot["retried_jobs"])
        telemetry_ingestion_oldest_pending_seconds.set(
            snapshot["oldest_pending_seconds"]
        )
        telemetry_ingestion_expired_leases.set(snapshot["expired_leases"])
        telemetry_ingestion_metrics_collection_success.set(1)

    def record_collection_failure(self) -> None:
        telemetry_ingestion_metrics_collection_success.set(0)
