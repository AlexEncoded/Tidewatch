from app.metrics import (
    telemetry_ingestion_attempts,
    telemetry_ingestion_expired_leases,
    telemetry_ingestion_jobs,
    telemetry_ingestion_metrics_collection_success,
    telemetry_ingestion_oldest_pending_seconds,
    telemetry_ingestion_retried_jobs,
)
from app.prometheus_telemetry_queue_metrics import PrometheusTelemetryQueueMetrics


def test_prometheus_queue_metrics_publish_snapshot_and_collection_status() -> None:
    publisher = PrometheusTelemetryQueueMetrics()
    statuses = ("pending", "processing", "completed", "failed")
    snapshot = {
        "pending": 1,
        "processing": 2,
        "completed": 3,
        "failed": 4,
        "pending_attempts": 5,
        "processing_attempts": 6,
        "completed_attempts": 7,
        "failed_attempts": 8,
        "retried_jobs": 9,
        "oldest_pending_seconds": 10,
        "expired_leases": 11,
    }
    labeled = (telemetry_ingestion_jobs, telemetry_ingestion_attempts)
    old_labeled_values = {
        (metric, status): metric.labels(status=status)._value.get()
        for metric in labeled
        for status in statuses
    }
    scalar_metrics = (
        telemetry_ingestion_retried_jobs,
        telemetry_ingestion_oldest_pending_seconds,
        telemetry_ingestion_expired_leases,
        telemetry_ingestion_metrics_collection_success,
    )
    old_scalar_values = {metric: metric._value.get() for metric in scalar_metrics}

    try:
        publisher.publish_snapshot(snapshot)

        for job_status in statuses:
            assert telemetry_ingestion_jobs.labels(status=job_status)._value.get() == snapshot[job_status]
            assert telemetry_ingestion_attempts.labels(
                status=job_status
            )._value.get() == snapshot[f"{job_status}_attempts"]
        assert telemetry_ingestion_retried_jobs._value.get() == 9
        assert telemetry_ingestion_oldest_pending_seconds._value.get() == 10
        assert telemetry_ingestion_expired_leases._value.get() == 11
        assert telemetry_ingestion_metrics_collection_success._value.get() == 1

        publisher.record_collection_failure()
        assert telemetry_ingestion_metrics_collection_success._value.get() == 0
    finally:
        for (metric, job_status), value in old_labeled_values.items():
            metric.labels(status=job_status).set(value)
        for metric, value in old_scalar_values.items():
            metric.set(value)
