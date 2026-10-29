from app.settings import telemetry_ingestion_is_queued


def test_telemetry_ingestion_defaults_to_synchronous_mode(monkeypatch) -> None:
    monkeypatch.delenv("TELEMETRY_INGESTION_MODE", raising=False)

    assert telemetry_ingestion_is_queued() is False


def test_telemetry_ingestion_mode_is_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("TELEMETRY_INGESTION_MODE", "QUEUED")

    assert telemetry_ingestion_is_queued() is True


def test_unknown_telemetry_ingestion_mode_remains_synchronous(monkeypatch) -> None:
    monkeypatch.setenv("TELEMETRY_INGESTION_MODE", "unknown")

    assert telemetry_ingestion_is_queued() is False
