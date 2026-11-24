"""HTTP dependency providers for system health and observability routes."""

from fastapi import Depends
from sqlalchemy.orm import Session

from ...application.system_ports import DatabaseHealthReader, MetricsScraper
from ...application.telemetry_ports import (
    TelemetryQueueMetricsPublisher,
    TelemetryQueueMetricsReader,
)
from ..postgres.database import get_db
from ..postgres.database_health import SQLDatabaseHealthReader
from ..postgres.telemetry_jobs import TelemetryIngestionJobRepository
from ..prometheus.metrics_scraper import PrometheusMetricsScraper
from ..prometheus.telemetry_queue_metrics import PrometheusTelemetryQueueMetrics


def get_database_health_reader(
    db: Session = Depends(get_db),
) -> DatabaseHealthReader:
    """Compose database-health checks with the SQL adapter."""
    return SQLDatabaseHealthReader(db)


def get_metrics_scraper() -> MetricsScraper:
    """Compose process-metric export with the Prometheus adapter."""
    return PrometheusMetricsScraper()


def get_telemetry_queue_metrics_reader(
    db: Session = Depends(get_db),
) -> TelemetryQueueMetricsReader:
    """Provide queue state as a read-only observability port."""
    return TelemetryIngestionJobRepository(db)


def get_telemetry_queue_metrics_publisher() -> TelemetryQueueMetricsPublisher:
    """Compose telemetry queue observability with Prometheus instruments."""
    return PrometheusTelemetryQueueMetrics()
