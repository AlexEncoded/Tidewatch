"""HTTP routes for system health and observability endpoints."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from ..adapter_dependencies import (
    get_database_health_reader,
    get_telemetry_queue_metrics_reader,
)
from ..application.system_ports import DatabaseHealthReader
from ..application.telemetry_ports import TelemetryQueueMetricsReader
from ..application.telemetry_queue_metrics import TelemetryQueueMetricsUnavailable
from ..metrics import (
    telemetry_ingestion_attempts,
    telemetry_ingestion_expired_leases,
    telemetry_ingestion_jobs,
    telemetry_ingestion_metrics_collection_success,
    telemetry_ingestion_oldest_pending_seconds,
    telemetry_ingestion_retried_jobs,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", tags=["system"])
def health(
    reader: DatabaseHealthReader = Depends(get_database_health_reader),
) -> dict[str, str]:
    reader.check_database()
    return {"status": "ok"}


@router.get("/metrics", include_in_schema=False)
def metrics(
    reader: TelemetryQueueMetricsReader = Depends(get_telemetry_queue_metrics_reader),
) -> Response:
    try:
        snapshot = reader.observability_snapshot()
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
    except TelemetryQueueMetricsUnavailable:
        telemetry_ingestion_metrics_collection_success.set(0)
        logger.exception("telemetry_queue_metrics_refresh_failed")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
