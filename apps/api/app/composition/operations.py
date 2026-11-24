"""Operations HTTP dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session
from ..application.maintenance_ports import MaintenanceMetrics, MaintenanceReader
from ..application.maintenance_notification_ports import MaintenanceNotificationJobStore
from ..application.quality_ports import QualitySummaryReader
from ..adapters.postgres.database import get_db
from ..adapters.postgres.quality_summary_repository import QualitySummaryRepository
from ..adapters.postgres.maintenance_notification_job_repository import (
    MaintenanceNotificationJobRepository,
)
from ..adapters.prometheus.maintenance_metrics import PrometheusMaintenanceMetrics
from ..adapters.postgres.maintenance_repository import MaintenanceRepository



def get_quality_summary_reader(
    db: Session = Depends(get_db),
) -> QualitySummaryReader:
    """Compose the quality-summary input port with its SQL adapter."""
    return QualitySummaryRepository(db)


def get_maintenance_reader(
    db: Session = Depends(get_db),
) -> MaintenanceReader:
    """Compose fleet maintenance queries with the SQL repository adapter."""
    return MaintenanceRepository(db)


def get_maintenance_metrics() -> MaintenanceMetrics:
    """Compose maintenance metrics with the Prometheus adapter."""
    return PrometheusMaintenanceMetrics()


def get_maintenance_notification_job_store(
    db: Session = Depends(get_db),
) -> MaintenanceNotificationJobStore:
    """Compose durable notification job storage with its SQL adapter."""
    return MaintenanceNotificationJobRepository(db)
