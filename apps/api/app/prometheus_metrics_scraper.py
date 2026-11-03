"""Prometheus adapter for rendering the process metrics endpoint."""

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .application.system_ports import MetricsScraper


class PrometheusMetricsScraper(MetricsScraper):
    """Render registered Prometheus instruments in the exposition format."""

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_LATEST

    def render(self) -> bytes:
        return generate_latest()
