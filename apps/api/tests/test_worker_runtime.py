from contextlib import contextmanager

from app.workers import runtime


def configure_runtime(monkeypatch, telemetry_result, notification_result):
    calls = []
    session = object()

    @contextmanager
    def session_scope():
        calls.append("open_session")
        yield session
        calls.append("close_session")

    monkeypatch.setattr(runtime, "SessionLocal", session_scope)
    monkeypatch.setattr(
        runtime,
        "TelemetryIngestionJobRepository",
        lambda db: calls.append(("telemetry_jobs", db)) or "telemetry_jobs",
    )
    monkeypatch.setattr(
        runtime,
        "TelemetryIngestionRepository",
        lambda db: calls.append(("telemetry_gateway", db)) or "telemetry_gateway",
    )
    monkeypatch.setattr(
        runtime,
        "SQLAlchemyTelemetryBatchUnitOfWork",
        lambda db: calls.append(("unit_of_work", db)) or "unit_of_work",
    )
    monkeypatch.setattr(
        runtime,
        "PrometheusTelemetryMetrics",
        lambda: calls.append("telemetry_metrics") or "telemetry_metrics",
    )
    monkeypatch.setattr(
        runtime,
        "MaintenanceNotificationJobRepository",
        lambda db: calls.append(("notification_jobs", db)) or "notification_jobs",
    )
    monkeypatch.setattr(
        runtime,
        "HttpxMaintenanceNotificationTransport",
        lambda: calls.append("notification_transport") or "notification_transport",
    )
    monkeypatch.setattr(runtime, "telemetry_job_lease_seconds", lambda: 30)
    monkeypatch.setattr(runtime, "telemetry_job_max_attempts", lambda: 4)
    monkeypatch.setattr(runtime, "maintenance_notification_lease_seconds", lambda: 30)
    monkeypatch.setattr(runtime, "maintenance_notification_max_attempts", lambda: 4)
    monkeypatch.setattr(runtime, "configured_maintenance_webhook_url", lambda: "https://hook")
    monkeypatch.setattr(
        runtime,
        "process_next_telemetry_job",
        lambda jobs, **kwargs: calls.append(("process_telemetry", jobs, kwargs))
        or telemetry_result,
    )
    monkeypatch.setattr(
        runtime,
        "process_next_maintenance_notification_job",
        lambda jobs, **kwargs: calls.append(("process_notification", jobs, kwargs))
        or notification_result,
    )
    return calls, session


def test_worker_cycle_composes_and_processes_both_queues(monkeypatch):
    calls, session = configure_runtime(monkeypatch, True, False)

    found_job = runtime.process_worker_cycle()

    assert found_job is True
    assert calls[0] == "open_session"
    assert ("telemetry_jobs", session) in calls
    assert ("telemetry_gateway", session) in calls
    assert ("unit_of_work", session) in calls
    assert ("notification_jobs", session) in calls
    assert any(call[0] == "process_telemetry" for call in calls if isinstance(call, tuple))
    assert any(call[0] == "process_notification" for call in calls if isinstance(call, tuple))
    assert calls[-1] == "close_session"


def test_worker_cycle_returns_false_when_both_queues_are_empty(monkeypatch):
    calls, _ = configure_runtime(monkeypatch, False, False)

    assert runtime.process_worker_cycle() is False
    assert any(call[0] == "process_telemetry" for call in calls if isinstance(call, tuple))
    assert any(call[0] == "process_notification" for call in calls if isinstance(call, tuple))

