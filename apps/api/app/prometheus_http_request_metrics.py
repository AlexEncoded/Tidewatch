"""Prometheus adapter for API request metrics."""

from .application.system_ports import HttpRequestMetrics
from .metrics import http_request_duration_seconds, http_requests_total


class PrometheusHttpRequestMetrics(HttpRequestMetrics):
    """Publish request count and duration using existing instruments."""

    def record_request(
        self, method: str, status_code: int, duration_seconds: float
    ) -> None:
        http_requests_total.labels(
            method=method, status_code=str(status_code)
        ).inc()
        http_request_duration_seconds.labels(method=method).observe(duration_seconds)
