"""Application-level failures for telemetry queue observability."""


class TelemetryQueueMetricsUnavailable(RuntimeError):
    """Raised when queue metrics cannot be read from their backing store."""
