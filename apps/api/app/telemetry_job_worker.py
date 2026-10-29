"""Durable queue consumer for telemetry batches."""

import logging
import os
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .adapter_dependencies import (
    get_telemetry_ingestion_gateway,
    get_telemetry_metrics,
)
from .application.telemetry_job_retry import telemetry_job_retry_delay_seconds
from .application.telemetry_batch import TelemetryBatchCommand
from .schemas.ingestion import TelemetryBatchCreate
from .application.telemetry_batch_ingestion import process_telemetry_batch
from .telemetry_ingestion_job_repository import TelemetryIngestionJobRepository
from .sqlalchemy_telemetry_unit_of_work import SQLAlchemyTelemetryBatchUnitOfWork
from .maintenance_notification_worker import process_next_maintenance_notification_job
from .settings import (
    telemetry_job_lease_seconds,
    telemetry_job_max_attempts,
    telemetry_job_poll_seconds,
)

logger = logging.getLogger(__name__)


def process_next_telemetry_job(db: Session) -> bool:
    """Process one queued batch; its sensor writes and completion commit together."""
    jobs = TelemetryIngestionJobRepository(db)
    now = datetime.now(timezone.utc)
    max_attempts = telemetry_job_max_attempts()
    job = jobs.claim_next(now, telemetry_job_lease_seconds(), max_attempts)
    if job is None:
        return False

    try:
        unit_of_work = SQLAlchemyTelemetryBatchUnitOfWork(db)

        def process_batch() -> None:
            payload = TelemetryBatchCreate.model_validate(job.payload)
            command = TelemetryBatchCommand.from_mapping(payload.model_dump())
            gateway = get_telemetry_ingestion_gateway(db)
            metrics = get_telemetry_metrics()
            process_telemetry_batch(
                job.buoy_id,
                command,
                gateway=gateway,
                unit_of_work=unit_of_work,
                metrics=metrics,
                jobs=None,
            )
            completed = jobs.complete(
                job.job_id, job.attempts, datetime.now(timezone.utc)
            )
            if completed is None:
                raise RuntimeError("Telemetry job lease expired before completion")

        unit_of_work.run_atomically(process_batch)
    except Exception as exc:
        failed = jobs.fail(
            job.job_id,
            job.attempts,
            str(exc),
            datetime.now(timezone.utc),
            max_attempts,
            retry_delay_seconds=telemetry_job_retry_delay_seconds(job.attempts),
        )
        if failed is None:
            logger.warning("Telemetry job %s lost its lease while failing", job.job_id)
        else:
            logger.exception(
                "Telemetry job %s failed on attempt %s (state=%s)",
                job.job_id,
                job.attempts,
                failed.status,
            )
    return True


def run_worker() -> None:
    """Poll PostgreSQL continuously using a fresh session per job."""
    from .database import SessionLocal

    while True:
        try:
            with SessionLocal() as db:
                found_telemetry_job = process_next_telemetry_job(db)
                found_notification_job = process_next_maintenance_notification_job(db)
                found_job = found_telemetry_job or found_notification_job
        except Exception:
            logger.exception("Telemetry queue polling failed; will retry")
            found_job = False
        if not found_job:
            time.sleep(telemetry_job_poll_seconds())


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_worker()
