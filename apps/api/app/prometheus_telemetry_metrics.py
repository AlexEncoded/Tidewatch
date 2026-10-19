"""Prometheus adapter for the application telemetry-metrics port."""

from prometheus_client.metrics import MetricWrapperBase

from . import metrics as prometheus_metrics


class PrometheusTelemetryMetrics:
    """Resolve application metric names to registered Prometheus instruments."""

    def metric(self, name: str) -> MetricWrapperBase:
        instrument = getattr(prometheus_metrics, name, None)
        if not isinstance(instrument, MetricWrapperBase):
            raise KeyError(f"Unknown telemetry metric: {name}")
        return instrument
