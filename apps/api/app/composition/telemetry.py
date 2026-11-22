"""Telemetry HTTP dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session
from ..application.telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionGateway,
    TelemetryMetrics,
    TelemetryQueueMetricsPublisher,
    TelemetryQueueMetricsReader,
)
from ..adapters.postgres.database import get_db
from ..adapters.postgres.telemetry_ingestion import TelemetryIngestionRepository
from ..adapters.postgres.telemetry_jobs import TelemetryIngestionJobRepository
from ..adapters.postgres.telemetry_unit_of_work import SQLAlchemyTelemetryBatchUnitOfWork
from ..adapters.prometheus.telemetry_metrics import PrometheusTelemetryMetrics
from ..adapters.prometheus.telemetry_queue_metrics import PrometheusTelemetryQueueMetrics



def get_telemetry_ingestion_gateway(
    db: Session = Depends(get_db),
) -> TelemetryIngestionGateway:
    """Compose batch telemetry writes with the SQL repository adapter."""
    return TelemetryIngestionRepository(db)


def get_telemetry_batch_unit_of_work(
    db: Session = Depends(get_db),
) -> TelemetryBatchUnitOfWork:
    """Compose the telemetry transaction port with its SQL adapter."""
    return SQLAlchemyTelemetryBatchUnitOfWork(db)


def get_telemetry_metrics() -> TelemetryMetrics:
    """Compose the telemetry metrics port with Prometheus instruments."""
    return PrometheusTelemetryMetrics()


def get_telemetry_ingestion_job_repository(
    db: Session = Depends(get_db),
) -> TelemetryIngestionJobRepository:
    """Provide the durable telemetry-job repository for HTTP operations."""
    return TelemetryIngestionJobRepository(db)


def get_telemetry_queue_metrics_reader(
    db: Session = Depends(get_db),
) -> TelemetryQueueMetricsReader:
    """Provide queue state as a read-only observability port."""
    return TelemetryIngestionJobRepository(db)


def get_telemetry_queue_metrics_publisher() -> TelemetryQueueMetricsPublisher:
    """Compose telemetry queue observability with its Prometheus adapter."""
    return PrometheusTelemetryQueueMetrics()
