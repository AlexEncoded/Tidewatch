"""Composition root for the background worker process."""

import logging
import os
import time

from ..adapters.postgres.database import SessionLocal
from ..adapters.postgres.maintenance_notification_job_repository import (
    MaintenanceNotificationJobRepository,
)
from ..adapters.postgres.telemetry_ingestion import TelemetryIngestionRepository
from ..adapters.postgres.telemetry_jobs import TelemetryIngestionJobRepository
from ..adapters.postgres.telemetry_unit_of_work import (
    SQLAlchemyTelemetryBatchUnitOfWork,
)
from ..adapters.webhook.maintenance_notifications import (
    HttpxMaintenanceNotificationTransport,
)
from ..adapters.prometheus.telemetry_metrics import PrometheusTelemetryMetrics
from ..settings import (
    configured_maintenance_webhook_url,
    maintenance_notification_lease_seconds,
    maintenance_notification_max_attempts,
    telemetry_job_lease_seconds,
    telemetry_job_max_attempts,
    telemetry_job_poll_seconds,
)
from .maintenance_notification_worker import process_next_maintenance_notification_job
from .telemetry_job_worker import process_next_telemetry_job

logger = logging.getLogger(__name__)


def process_worker_cycle() -> bool:
    """Poll each durable queue once using a fresh database session."""
    with SessionLocal() as db:
        found_telemetry_job = process_next_telemetry_job(
            TelemetryIngestionJobRepository(db),
            gateway=TelemetryIngestionRepository(db),
            unit_of_work=SQLAlchemyTelemetryBatchUnitOfWork(db),
            metrics=PrometheusTelemetryMetrics(),
            lease_seconds=telemetry_job_lease_seconds(),
            max_attempts=telemetry_job_max_attempts(),
        )
        found_notification_job = process_next_maintenance_notification_job(
            MaintenanceNotificationJobRepository(db),
            transport=HttpxMaintenanceNotificationTransport(),
            webhook_url=configured_maintenance_webhook_url(),
            lease_seconds=maintenance_notification_lease_seconds(),
            max_attempts=maintenance_notification_max_attempts(),
        )
    return found_telemetry_job or found_notification_job


def run_worker() -> None:
    """Poll durable queues continuously and wait when both are empty."""
    while True:
        try:
            found_job = process_worker_cycle()
        except Exception:
            logger.exception("Worker queue polling failed; will retry")
            found_job = False
        if not found_job:
            time.sleep(telemetry_job_poll_seconds())


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_worker()
