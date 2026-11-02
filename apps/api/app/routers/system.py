"""HTTP routes for system health and observability endpoints."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from ..adapter_dependencies import (
    get_database_health_reader,
    get_telemetry_queue_metrics_reader,
    get_telemetry_queue_metrics_publisher,
)
from ..application.system_ports import DatabaseHealthReader
from ..application.telemetry_ports import (
    TelemetryQueueMetricsPublisher,
    TelemetryQueueMetricsReader,
)
from ..application.telemetry_queue_metrics import TelemetryQueueMetricsUnavailable


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
    publisher: TelemetryQueueMetricsPublisher = Depends(
        get_telemetry_queue_metrics_publisher
    ),
) -> Response:
    try:
        snapshot = reader.observability_snapshot()
        publisher.publish_snapshot(snapshot)
    except TelemetryQueueMetricsUnavailable:
        publisher.record_collection_failure()
        logger.exception("telemetry_queue_metrics_refresh_failed")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
