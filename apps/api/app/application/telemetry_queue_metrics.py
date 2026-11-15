"""Application-level failures for telemetry queue observability."""

from .telemetry_ports import (
    TelemetryQueueMetricsPublisher,
    TelemetryQueueMetricsReader,
)


class TelemetryQueueMetricsUnavailable(RuntimeError):
    """Raised when queue metrics cannot be read from their backing store."""


def refresh_telemetry_queue_metrics(
    reader: TelemetryQueueMetricsReader,
    publisher: TelemetryQueueMetricsPublisher,
) -> None:
    """Read and publish queue metrics, recording unavailable collections."""
    try:
        snapshot = reader.observability_snapshot()
        publisher.publish_snapshot(snapshot)
    except TelemetryQueueMetricsUnavailable:
        publisher.record_collection_failure()
        raise
