from datetime import datetime, timezone

from app.application.marine_current_ingestion import ingest_marine_current_reading
from app.domain.marine_current import MarineCurrentTelemetrySnapshot


class FakeMetrics:
    def __init__(self) -> None:
        self.events = []
        self.metric_name = None
        self.labels_value = None

    def metric(self, name: str):
        self.metric_name = name
        return self

    def labels(self, **labels):
        self.labels_value = labels
        return self

    def inc(self, amount: float = 1) -> None:
        self.events.append((self.metric_name, self.labels_value, "inc", amount))

    def set(self, value: float) -> None:
        self.events.append((self.metric_name, self.labels_value, "set", value))


class FakeGateway:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists
        self.events = []

    def buoy_exists(self, buoy_id: str) -> bool:
        self.events.append(("exists", buoy_id))
        return self.exists

    def add_marine_current(self, reading: MarineCurrentTelemetrySnapshot):
        self.events.append(("add", reading))
        return reading


def test_ingestion_persists_reading_and_publishes_heartbeat_and_metrics() -> None:
    measured_at = datetime(2026, 11, 11, tzinfo=timezone.utc)
    received_at = datetime(2026, 11, 11, 0, 1, tzinfo=timezone.utc)
    reading = MarineCurrentTelemetrySnapshot("buoy-1", 1.7, 142.0, measured_at)
    gateway = FakeGateway()
    metrics = FakeMetrics()

    saved = ingest_marine_current_reading(gateway, metrics, reading, received_at)

    assert saved is reading
    assert gateway.events == [("exists", "buoy-1"), ("add", reading)]
    assert (
        "buoy_last_seen_timestamp_seconds",
        {"buoy_id": "buoy-1"},
        "set",
        received_at.timestamp(),
    ) in metrics.events
    assert (
        "marine_current_readings_total",
        {"buoy_id": "buoy-1", "sensor_channel": "A"},
        "inc",
        1,
    ) in metrics.events
    assert {
        (name, operation, value)
        for name, _, operation, value in metrics.events
        if name in {
            "current_marine_current_speed_mps",
            "current_marine_current_direction_degrees",
        }
    } == {
        ("current_marine_current_speed_mps", "set", 1.7),
        ("current_marine_current_direction_degrees", "set", 142.0),
    }


def test_ingestion_skips_persistence_and_metrics_for_unknown_buoy() -> None:
    reading = MarineCurrentTelemetrySnapshot(
        "missing", 1.7, 142.0, datetime(2026, 11, 11, tzinfo=timezone.utc)
    )
    gateway = FakeGateway(exists=False)
    metrics = FakeMetrics()

    assert ingest_marine_current_reading(gateway, metrics, reading) is None
    assert gateway.events == [("exists", "missing")]
    assert metrics.events == []
