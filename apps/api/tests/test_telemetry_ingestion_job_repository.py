from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.entities import BuoyEntity
from app.telemetry_ingestion_job_repository import TelemetryIngestionJobRepository


@pytest.fixture
def job_repository():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(
            BuoyEntity(
                id="TW-JOB",
                name="Queue test buoy",
                status="active",
                created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            )
        )
        db.commit()
        yield TelemetryIngestionJobRepository(db)
    engine.dispose()


def test_enqueue_creates_pending_job_with_payload(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    payload = {"temperatures": [{"temperature_celsius": 19.5}]}

    job = job_repository.enqueue("TW-JOB", payload, now)

    assert len(job.job_id) == 32
    assert job.buoy_id == "TW-JOB"
    assert job.payload == payload
    assert job.status == "pending"
    assert job.attempts == 0
    assert job_repository.get(job.job_id) == job


def test_claim_sets_processing_lease_and_prevents_early_reclaim(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    enqueued = job_repository.enqueue("TW-JOB", {}, now)

    claimed = job_repository.claim_next(now, lease_seconds=30)

    assert claimed is not None
    assert claimed.job_id == enqueued.job_id
    assert claimed.status == "processing"
    assert claimed.attempts == 1
    assert claimed.lease_expires_at.replace(tzinfo=timezone.utc) == now + timedelta(seconds=30)
    assert job_repository.claim_next(now + timedelta(seconds=29), 30) is None


def test_expired_lease_can_be_reclaimed(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    job_repository.enqueue("TW-JOB", {}, now)
    first_claim = job_repository.claim_next(now, lease_seconds=10)

    reclaimed = job_repository.claim_next(now + timedelta(seconds=10), lease_seconds=10)

    assert reclaimed is not None
    assert reclaimed.job_id == first_claim.job_id
    assert reclaimed.attempts == 2
    assert reclaimed.status == "processing"


def test_worker_can_renew_only_its_active_lease(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    enqueued = job_repository.enqueue("TW-JOB", {}, now)
    claimed = job_repository.claim_next(now, lease_seconds=10)

    renewed = job_repository.renew_lease(
        enqueued.job_id, claimed.attempts, now + timedelta(seconds=5), 20
    )
    stale_renewal = job_repository.renew_lease(
        enqueued.job_id, claimed.attempts - 1, now + timedelta(seconds=5), 20
    )

    assert renewed.lease_expires_at.replace(tzinfo=timezone.utc) == now + timedelta(seconds=25)
    assert stale_renewal is None


def test_failure_schedules_retry_then_marks_exhausted_job_failed(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    enqueued = job_repository.enqueue("TW-JOB", {}, now)
    first_attempt = job_repository.claim_next(now, lease_seconds=10)

    retry = job_repository.fail(
        first_attempt.job_id,
        first_attempt.attempts,
        "temporary",
        now,
        max_attempts=2,
        retry_delay_seconds=5,
    )

    assert retry.status == "pending"
    assert retry.available_at.replace(tzinfo=timezone.utc) == now + timedelta(seconds=5)
    assert job_repository.claim_next(now + timedelta(seconds=4), 10) is None
    second_attempt = job_repository.claim_next(now + timedelta(seconds=5), 10)
    failed = job_repository.fail(
        second_attempt.job_id,
        second_attempt.attempts,
        "permanent",
        now + timedelta(seconds=5),
        max_attempts=2,
        retry_delay_seconds=5,
    )

    assert failed.status == "failed"
    assert failed.last_error == "permanent"
    assert job_repository.claim_next(now + timedelta(days=1), 10) is None
    assert job_repository.get(enqueued.job_id).status == "failed"


def test_completion_only_applies_to_a_processing_job(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    enqueued = job_repository.enqueue("TW-JOB", {}, now)

    assert job_repository.complete(enqueued.job_id, 0, now) is None
    claimed = job_repository.claim_next(now, lease_seconds=10)
    completed = job_repository.complete(enqueued.job_id, claimed.attempts, now)

    assert completed.status == "completed"
    assert completed.completed_at.replace(tzinfo=timezone.utc) == now
    assert completed.lease_expires_at is None


def test_invalid_lease_and_retry_policy_are_rejected(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="lease"):
        job_repository.claim_next(now, lease_seconds=0)

    job = job_repository.enqueue("TW-JOB", {}, now)
    claimed = job_repository.claim_next(now, lease_seconds=10)
    with pytest.raises(ValueError, match="Retry attempts"):
        job_repository.fail(
            claimed.job_id,
            claimed.attempts,
            "temporary",
            now,
            max_attempts=0,
            retry_delay_seconds=0,
        )

    assert job_repository.get(job.job_id).status == "processing"


def test_expired_job_is_terminal_after_maximum_claims(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    enqueued = job_repository.enqueue("TW-JOB", {}, now)
    job_repository.claim_next(now, lease_seconds=1, max_attempts=2)
    job_repository.claim_next(
        now + timedelta(seconds=1), lease_seconds=1, max_attempts=2
    )

    assert (
        job_repository.claim_next(
            now + timedelta(seconds=2), lease_seconds=1, max_attempts=2
        )
        is None
    )
    terminal = job_repository.get(enqueued.job_id)
    assert terminal.status == "failed"
    assert terminal.last_error == "Worker lease expired after maximum attempts"


def test_stale_worker_attempt_cannot_finish_a_reclaimed_job(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    enqueued = job_repository.enqueue("TW-JOB", {}, now)
    first_attempt = job_repository.claim_next(now, lease_seconds=1)
    second_attempt = job_repository.claim_next(now + timedelta(seconds=1), lease_seconds=10)

    assert job_repository.complete(
        enqueued.job_id, first_attempt.attempts, now + timedelta(seconds=2)
    ) is None
    assert job_repository.fail(
        enqueued.job_id,
        first_attempt.attempts,
        "stale failure",
        now + timedelta(seconds=2),
        max_attempts=5,
        retry_delay_seconds=1,
    ) is None
    assert job_repository.get(enqueued.job_id).status == "processing"
    assert second_attempt.attempts == 2
