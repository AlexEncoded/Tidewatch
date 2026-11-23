"""Composition root for the background worker process."""

import logging
import os
import time

from ..adapters.postgres.database import SessionLocal
from ..settings import telemetry_job_poll_seconds
from .maintenance_notification_worker import process_next_maintenance_notification_job
from .telemetry_job_worker import process_next_telemetry_job

logger = logging.getLogger(__name__)


def run_worker() -> None:
    """Poll durable queues using a fresh database session for each cycle."""
    while True:
        try:
            with SessionLocal() as db:
                found_telemetry_job = process_next_telemetry_job(db)
                found_notification_job = process_next_maintenance_notification_job(db)
                found_job = found_telemetry_job or found_notification_job
        except Exception:
            logger.exception("Worker queue polling failed; will retry")
            found_job = False
        if not found_job:
            time.sleep(telemetry_job_poll_seconds())


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_worker()
