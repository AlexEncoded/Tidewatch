from types import SimpleNamespace

import pytest

from app.application.telemetry_queue_metrics import (
    TelemetryQueueMetricsUnavailable,
    refresh_telemetry_queue_metrics,
)


def test_queue_metrics_refresh_publishes_the_reader_snapshot() -> None:
    snapshot = SimpleNamespace(pending=3)
    events = []

    class Reader:
        def observability_snapshot(self):
            events.append("read")
            return snapshot

    class Publisher:
        def publish_snapshot(self, value):
            events.append(("publish", value))

        def record_collection_failure(self):
            raise AssertionError("successful collection must not record failure")

    assert refresh_telemetry_queue_metrics(Reader(), Publisher()) is None
    assert events == ["read", ("publish", snapshot)]


def test_queue_metrics_refresh_records_collection_failure() -> None:
    events = []

    class Reader:
        def observability_snapshot(self):
            raise TelemetryQueueMetricsUnavailable

    class Publisher:
        def publish_snapshot(self, value):
            raise AssertionError("unavailable snapshot must not be published")

        def record_collection_failure(self):
            events.append("failure")

    with pytest.raises(TelemetryQueueMetricsUnavailable):
        refresh_telemetry_queue_metrics(Reader(), Publisher())
    assert events == ["failure"]
