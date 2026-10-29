from app.settings import (
    configured_maintenance_webhook_url,
    telemetry_ingestion_is_queued,
)


def test_telemetry_ingestion_defaults_to_synchronous_mode(monkeypatch) -> None:
    monkeypatch.delenv("TELEMETRY_INGESTION_MODE", raising=False)

    assert telemetry_ingestion_is_queued() is False


def test_telemetry_ingestion_mode_is_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("TELEMETRY_INGESTION_MODE", "QUEUED")

    assert telemetry_ingestion_is_queued() is True


def test_unknown_telemetry_ingestion_mode_remains_synchronous(monkeypatch) -> None:
    monkeypatch.setenv("TELEMETRY_INGESTION_MODE", "unknown")

    assert telemetry_ingestion_is_queued() is False


def test_maintenance_webhook_url_is_optional(monkeypatch) -> None:
    monkeypatch.delenv("MAINTENANCE_WEBHOOK_URL", raising=False)

    assert configured_maintenance_webhook_url() is None


def test_maintenance_webhook_url_returns_configured_value(monkeypatch) -> None:
    monkeypatch.setenv("MAINTENANCE_WEBHOOK_URL", "https://hooks.example.test/tidewatch")

    assert configured_maintenance_webhook_url() == "https://hooks.example.test/tidewatch"
