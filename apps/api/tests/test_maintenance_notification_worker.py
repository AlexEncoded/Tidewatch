from datetime import datetime, timezone
from types import SimpleNamespace

from app.workers.maintenance_notification_worker import (
    process_next_maintenance_notification_job,
)


class FakeJobStore:
    _use_job_as_completion = object()

    def __init__(self, job=None, *, completion_result=_use_job_as_completion):
        self.job = job
        self.completion_result = (
            job
            if completion_result is self._use_job_as_completion
            else completion_result
        )
        self.claim = None
        self.completed = None
        self.failure = None

    def claim_next(self, now, lease_seconds, max_attempts):
        self.claim = (now, lease_seconds, max_attempts)
        return self.job

    def complete(self, job_id, attempt, now):
        self.completed = (job_id, attempt, now)
        return self.completion_result

    def fail(
        self,
        job_id,
        attempt,
        error_code,
        now,
        max_attempts,
        retry_delay_seconds,
    ):
        self.failure = (
            job_id,
            attempt,
            error_code,
            now,
            max_attempts,
            retry_delay_seconds,
        )
        self.job.status = "pending"
        return self.job


class FakeResponse:
    def raise_for_status(self):
        return None


def make_job(attempts=1):
    return SimpleNamespace(
        job_id="notification-1",
        payload={"source": "tidewatch", "issues": []},
        attempts=attempts,
        status="processing",
    )


def process(store, transport, *, webhook_url="https://hooks.example.test/tidewatch"):
    return process_next_maintenance_notification_job(
        store,
        transport=transport,
        webhook_url=webhook_url,
        lease_seconds=30,
        max_attempts=4,
        now=datetime(2026, 11, 24, tzinfo=timezone.utc),
    )


def test_worker_returns_false_when_no_notification_is_available():
    store = FakeJobStore()

    assert process(store, lambda *_args, **_kwargs: FakeResponse()) is False
    assert store.claim == (datetime(2026, 11, 24, tzinfo=timezone.utc), 30, 4)
    assert store.completed is None
    assert store.failure is None


def test_worker_delivers_and_completes_claimed_notification():
    job = make_job()
    store = FakeJobStore(job)
    delivered = {}

    def transport(url, *, json, timeout):
        delivered.update(url=url, payload=json, timeout=timeout)
        return FakeResponse()

    assert process(store, transport) is True
    assert delivered == {
        "url": "https://hooks.example.test/tidewatch",
        "payload": job.payload,
        "timeout": 5,
    }
    assert store.completed is not None
    assert store.completed[:2] == (job.job_id, job.attempts)
    assert store.completed[2].tzinfo is not None
    assert store.failure is None


def test_worker_marks_missing_webhook_as_configuration_failure():
    job = make_job()
    store = FakeJobStore(job)
    transport_calls = []

    assert process(
        store,
        lambda *args, **kwargs: transport_calls.append((args, kwargs)),
        webhook_url=None,
    )
    assert transport_calls == []
    assert store.failure is not None
    assert store.failure[2] == "webhook_not_configured"
    assert store.failure[4:] == (4, 2)


def test_worker_retries_failed_delivery_with_capped_domain_backoff():
    job = make_job(attempts=3)
    store = FakeJobStore(job)

    def failing_transport(*_args, **_kwargs):
        raise TimeoutError("destination unavailable")

    assert process(store, failing_transport) is True
    assert store.completed is None
    assert store.failure is not None
    assert store.failure[2] == "delivery_failed"
    assert store.failure[4:] == (4, 8)


def test_worker_retries_when_claim_lease_expires_before_completion():
    job = make_job()
    store = FakeJobStore(job, completion_result=None)

    assert process(store, lambda *_args, **_kwargs: FakeResponse()) is True
    assert store.failure is not None
    assert store.failure[2] == "notification_job_lease_expired"
