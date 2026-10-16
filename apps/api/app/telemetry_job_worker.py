"""Durable queue consumer for telemetry batches."""

import logging
import os
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from starlette.responses import Response

from .adapter_dependencies import get_telemetry_ingestion_gateway
from .routers.ingestion import ingest_telemetry
from .schemas.ingestion import TelemetryBatchCreate
from .telemetry_ingestion_job_repository import TelemetryIngestionJobRepository

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

    db.info["tidewatch_defer_repository_commits"] = True
    try:
        payload = TelemetryBatchCreate.model_validate(job.payload)
        gateway = get_telemetry_ingestion_gateway(db)
        ingest_telemetry(
            job.buoy_id,
            payload,
            Response(),
            gateway=gateway,
            jobs=None,
        )
        completed = jobs.complete(job.job_id, job.attempts, datetime.now(timezone.utc))
        if completed is None:
            raise RuntimeError("Telemetry job lease expired before completion")
        db.info.pop("tidewatch_defer_repository_commits", None)
        db.commit()
    except Exception as exc:
        db.info.pop("tidewatch_defer_repository_commits", None)
        db.rollback()
        failed = jobs.fail(
            job.job_id,
            job.attempts,
            str(exc),
            datetime.now(timezone.utc),
            JOB_MAX_ATTEMPTS,
            retry_delay_seconds=min(300, 2 ** job.attempts),
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
