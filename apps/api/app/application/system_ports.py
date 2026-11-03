"""Application input ports for system-level health checks."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DatabaseHealthReader(Protocol):
    """Check whether the primary database can answer queries."""

    def check_database(self) -> None:
        ...


class AvailabilityMetrics(Protocol):
    """Restore buoy and physical-device heartbeat metric series at startup."""

    def clear(self) -> None:
        ...

    def restore_device_heartbeat(
        self,
        buoy_id: str,
        device_id: str,
        sensor_channel: str,
        timestamp_seconds: float,
    ) -> None:
        ...

    def restore_buoy_heartbeat(self, buoy_id: str, timestamp_seconds: float) -> None:
        ...


class HttpRequestMetrics(Protocol):
    """Record request volume and elapsed time for the API process."""

    def record_request(
        self, method: str, status_code: int, duration_seconds: float
    ) -> None:
        ...


class MetricsScraper(Protocol):
    """Render the process metrics payload and its media type."""

    def render(self) -> bytes:
        ...

    @property
    def content_type(self) -> str:
        ...
