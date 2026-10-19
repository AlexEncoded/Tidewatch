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

logger = logging.getLogger(__name__)
JOB_LEASE_SECONDS = max(1, int(os.getenv("TELEMETRY_JOB_LEASE_SECONDS", "300")))
JOB_MAX_ATTEMPTS = max(1, int(os.getenv("TELEMETRY_JOB_MAX_ATTEMPTS", "5")))
JOB_POLL_SECONDS = max(0.1, float(os.getenv("TELEMETRY_JOB_POLL_SECONDS", "2")))


def process_next_telemetry_job(db: Session) -> bool:
    """Process one queued batch; its sensor writes and completion commit together."""
    jobs = TelemetryIngestionJobRepository(db)
    now = datetime.now(timezone.utc)
    job = jobs.claim_next(now, JOB_LEASE_SECONDS, JOB_MAX_ATTEMPTS)
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
            JOB_MAX_ATTEMPTS,
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
                found_job = process_next_telemetry_job(db)
        except Exception:
            logger.exception("Telemetry queue polling failed; will retry")
            found_job = False
        if not found_job:
            time.sleep(JOB_POLL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_worker()
