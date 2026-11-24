"""Telemetry HTTP dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session
from ...application.telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionGateway,
    TelemetryMetrics,
)
from ..postgres.database import get_db
from ..postgres.telemetry_ingestion import TelemetryIngestionRepository
from ..postgres.telemetry_jobs import TelemetryIngestionJobRepository
from ..postgres.telemetry_unit_of_work import SQLAlchemyTelemetryBatchUnitOfWork
from ..prometheus.telemetry_metrics import PrometheusTelemetryMetrics



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
