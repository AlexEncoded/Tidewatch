from datetime import datetime, timezone
from types import SimpleNamespace

from app.workers import telemetry_job_worker


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
        self.complete_during_transaction = None

    def claim_next(self, now, lease_seconds, max_attempts):
        self.claim = (now, lease_seconds, max_attempts)
        return self.job

    def complete(self, job_id, attempt, now):
        self.completed = (job_id, attempt, now)
        self.complete_during_transaction = FakeUnitOfWork.active
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
        return SimpleNamespace(status="pending")


class FakeUnitOfWork:
    active = False

    def run_atomically(self, action):
        self.active = True
        FakeUnitOfWork.active = True
        try:
            return action()
        finally:
            self.active = False
            FakeUnitOfWork.active = False


def make_job(attempts=1):
    return SimpleNamespace(
        job_id="telemetry-1",
        buoy_id="TW-1",
        payload={"temperatures": [{"temperature_celsius": 18.5}]},
        attempts=attempts,
        created_at=datetime(2026, 11, 23, tzinfo=timezone.utc),
    )


def process(store, *, monkeypatch, process_batch=None):
    unit_of_work = FakeUnitOfWork()
    captured = {}

    def fake_process(buoy_id, command, **kwargs):
        captured.update(buoy_id=buoy_id, command=command, **kwargs)
        if process_batch is not None:
            process_batch()

    monkeypatch.setattr(telemetry_job_worker, "process_telemetry_batch", fake_process)
    result = telemetry_job_worker.process_next_telemetry_job(
        store,
        gateway=object(),
        unit_of_work=unit_of_work,
        metrics=object(),
        lease_seconds=30,
        max_attempts=4,
        now=datetime(2026, 11, 24, tzinfo=timezone.utc),
    )
    return result, captured


def test_worker_returns_false_when_no_telemetry_job_is_available(monkeypatch):
    store = FakeJobStore()

    result, _ = process(store, monkeypatch=monkeypatch)

    assert result is False
    assert store.claim == (datetime(2026, 11, 24, tzinfo=timezone.utc), 30, 4)
    assert store.completed is None
    assert store.failure is None


def test_worker_processes_batch_and_completes_job_inside_transaction(monkeypatch):
    job = make_job()
    store = FakeJobStore(job)

    result, captured = process(store, monkeypatch=monkeypatch)

    assert result is True
    assert captured["buoy_id"] == "TW-1"
    reading = captured["command"].readings["temperatures"][0]
    assert reading["temperature_celsius"] == 18.5
    assert isinstance(reading["measured_at"], datetime)
    assert captured["clock_observation_at"] == job.created_at
    assert store.completed is not None
    assert store.completed[:2] == (job.job_id, job.attempts)
    assert store.complete_during_transaction is True
    assert store.failure is None


def test_worker_retries_failed_batch_with_domain_backoff(monkeypatch):
    job = make_job(attempts=3)
    store = FakeJobStore(job)

    def fail_batch():
        raise ValueError("invalid telemetry")

    result, _ = process(store, monkeypatch=monkeypatch, process_batch=fail_batch)

    assert result is True
    assert store.completed is None
    assert store.failure is not None
    assert store.failure[2] == "invalid telemetry"
    assert store.failure[4:] == (4, 8)


def test_worker_retries_if_job_lease_expires_before_atomic_completion(monkeypatch):
    job = make_job()
    store = FakeJobStore(job, completion_result=None)

    result, _ = process(store, monkeypatch=monkeypatch)

    assert result is True
    assert store.complete_during_transaction is True
    assert store.failure is not None
    assert store.failure[2] == "Telemetry job lease expired before completion"
