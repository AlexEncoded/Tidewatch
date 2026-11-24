"""Durable queue consumer for telemetry batches."""

import logging
from datetime import datetime, timezone

from ..application.telemetry_batch import TelemetryBatchCommand
from ..application.telemetry_batch_ingestion import process_telemetry_batch
from ..application.telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionGateway,
    TelemetryIngestionJobStore,
    TelemetryMetrics,
)
from ..domain.telemetry_job_retry import telemetry_job_retry_delay_seconds

logger = logging.getLogger(__name__)


def process_next_telemetry_job(
    jobs: TelemetryIngestionJobStore,
    *,
    gateway: TelemetryIngestionGateway,
    unit_of_work: TelemetryBatchUnitOfWork,
    metrics: TelemetryMetrics,
    lease_seconds: int,
    max_attempts: int,
    now: datetime | None = None,
) -> bool:
    """Process one queued batch; its sensor writes and completion commit together."""
    claimed_at = now or datetime.now(timezone.utc)
    job = jobs.claim_next(claimed_at, lease_seconds, max_attempts)
    if job is None:
        return False

    try:
        def process_batch() -> None:
            command = TelemetryBatchCommand.from_json_mapping(job.payload)
            process_telemetry_batch(
                job.buoy_id,
                command,
                gateway=gateway,
                unit_of_work=unit_of_work,
                metrics=metrics,
                jobs=None,
                clock_observation_at=(
                    job.created_at.replace(tzinfo=timezone.utc)
                    if job.created_at.tzinfo is None
                    else job.created_at
                ),
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
