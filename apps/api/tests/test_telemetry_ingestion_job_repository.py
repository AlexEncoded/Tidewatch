from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.database import Base, TidewatchSession
from app.application.telemetry_queue_metrics import TelemetryQueueMetricsUnavailable
from app.entities import BuoyEntity, TemperatureReadingEntity
from app.routers.ingestion import _atomic_telemetry_batch
from app.telemetry_ingestion_job_repository import TelemetryIngestionJobRepository
from app.telemetry_job_worker import process_next_telemetry_job


@pytest.fixture
def job_repository():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, class_=TidewatchSession)() as db:
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


def test_enqueue_returns_existing_job_for_repeated_idempotency_key(job_repository) -> None:
    first = job_repository.enqueue(
        "TW-JOB", {"temperatures": [{"temperature_celsius": 19.5}]},
        idempotency_key="simulator-cycle-1",
    )
    repeated = job_repository.enqueue(
        "TW-JOB", {"temperatures": [{"temperature_celsius": 20.5}]},
        idempotency_key="simulator-cycle-1",
    )

    assert repeated.job_id == first.job_id
    assert repeated.payload == first.payload
    assert repeated.idempotency_key == "simulator-cycle-1"


def test_idempotency_key_is_scoped_to_its_buoy(job_repository) -> None:
    job_repository.db.add(
        BuoyEntity(
            id="TW-JOB-2",
            name="Second queue test buoy",
            status="active",
            created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
    )
    job_repository.db.commit()

    first = job_repository.enqueue(
        "TW-JOB", {"temperatures": []}, idempotency_key="cycle-1"
    )
    second = job_repository.enqueue(
        "TW-JOB-2", {"temperatures": []}, idempotency_key="cycle-1"
    )

    assert first.job_id != second.job_id
    assert first.buoy_id == "TW-JOB"
    assert second.buoy_id == "TW-JOB-2"


def test_observability_snapshot_reports_queue_depth_and_expired_leases(job_repository) -> None:
    now = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
    job_repository.enqueue("TW-JOB", {}, now)
    job_repository.claim_next(now, lease_seconds=10)

    snapshot = job_repository.observability_snapshot(now + timedelta(seconds=70))

    assert snapshot["pending"] == 0
    assert snapshot["processing"] == 1
    assert snapshot["oldest_pending_seconds"] == 0
    assert snapshot["expired_leases"] == 1


def test_observability_snapshot_translates_database_errors_and_rolls_back() -> None:
    class BrokenSession:
        rolled_back = False

        def execute(self, statement):
            raise SQLAlchemyError("database unavailable")

        def rollback(self) -> None:
            self.rolled_back = True

    db = BrokenSession()
    repository = TelemetryIngestionJobRepository(db)

    with pytest.raises(TelemetryQueueMetricsUnavailable) as raised:
        repository.observability_snapshot()

    assert isinstance(raised.value.__cause__, SQLAlchemyError)
    assert db.rolled_back


def test_telemetry_batch_rolls_back_repository_commits_on_failure(job_repository) -> None:
    db = job_repository.db
    gateway = type("Gateway", (), {"db": db})()

    @_atomic_telemetry_batch
    def persist_then_fail(gateway) -> None:
        gateway.db.add(
            BuoyEntity(
                id="TW-ROLLBACK",
                name="Must not persist",
                status="active",
                created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            )
        )
        gateway.db.commit()
        raise RuntimeError("simulated batch failure")

    assert isinstance(db, TidewatchSession)
    with pytest.raises(RuntimeError, match="simulated batch failure"):
        persist_then_fail(gateway)

    assert db.get(BuoyEntity, "TW-ROLLBACK") is None


def test_worker_processes_job_and_commits_readings_with_completion(job_repository) -> None:
    job = job_repository.enqueue(
        "TW-JOB", {"temperatures": [{"temperature_celsius": 19.5}]}
    )

    assert process_next_telemetry_job(job_repository.db) is True

    completed = job_repository.get(job.job_id)
    assert completed is not None
    assert completed.status == "completed"
    assert job_repository.db.query(TemperatureReadingEntity).count() == 1


def test_worker_retries_invalid_batch_without_persisting_readings(job_repository) -> None:
    job = job_repository.enqueue(
        "TW-JOB", {"temperatures": [{"temperature_celsius": 999}]}
    )

    assert process_next_telemetry_job(job_repository.db) is True

    failed_attempt = job_repository.get(job.job_id)
    assert failed_attempt is not None
    assert failed_attempt.status == "pending"
    assert failed_attempt.attempts == 1
    assert "temperature_celsius" in failed_attempt.last_error
    assert job_repository.db.query(TemperatureReadingEntity).count() == 0


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
