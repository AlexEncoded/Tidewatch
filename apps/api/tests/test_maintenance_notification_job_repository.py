from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, TidewatchSession
from app.maintenance_notification_job_repository import (
    MaintenanceNotificationIdempotencyConflict,
    MaintenanceNotificationJobRepository,
)


@pytest.fixture
def repository():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, class_=TidewatchSession)() as db:
        yield MaintenanceNotificationJobRepository(db)
    engine.dispose()


def test_enqueue_is_idempotent_and_rejects_key_reuse_with_different_payload(repository):
    now = datetime(2026, 10, 26, 10, tzinfo=timezone.utc)
    payload = {"source": "tidewatch", "issues": [{"issue_type": "stale_buoy"}]}
    first = repository.enqueue("request-1", payload, 1, now)
    repeated = repository.enqueue("request-1", payload, 1, now)

    assert repeated.job_id == first.job_id
    assert repeated.status == "pending"
    assert repeated.payload == payload
    with pytest.raises(MaintenanceNotificationIdempotencyConflict):
        repository.enqueue("request-1", {"source": "other", "issues": []}, 0, now)


def test_claim_failure_retry_and_completion_are_persisted(repository):
    now = datetime.now(timezone.utc)
    queued = repository.enqueue("request-2", {"issues": []}, 0, now)
    claimed = repository.claim_next(now, lease_seconds=30, max_attempts=3)

    retry = repository.fail(
        claimed.job_id,
        claimed.attempts,
        "delivery_failed",
        now,
        max_attempts=3,
        retry_delay_seconds=5,
    )
    assert retry.status == "pending"
    assert retry.last_error == "delivery_failed"
    assert retry.available_at.replace(tzinfo=timezone.utc) == now + timedelta(seconds=5)
    assert repository.claim_next(now + timedelta(seconds=4), 30, 3) is None

    second_attempt = repository.claim_next(now + timedelta(seconds=5), 30, 3)
    sent = repository.complete(
        second_attempt.job_id,
        second_attempt.attempts,
        now + timedelta(seconds=6),
    )
    assert sent.status == "sent"
    assert sent.completed_at.replace(tzinfo=timezone.utc) == now + timedelta(seconds=6)
    assert repository.get(queued.job_id).status == "sent"


def test_expired_notification_lease_can_be_reclaimed(repository):
    now = datetime.now(timezone.utc)
    queued = repository.enqueue("request-3", {"issues": []}, 0, now)
    first = repository.claim_next(now, lease_seconds=5, max_attempts=3)

    reclaimed = repository.claim_next(now + timedelta(seconds=5), 5, 3)

    assert reclaimed.job_id == queued.job_id == first.job_id
    assert reclaimed.attempts == 2
    assert reclaimed.status == "processing"
