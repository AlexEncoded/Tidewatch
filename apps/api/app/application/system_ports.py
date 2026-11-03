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

    def record_device_heartbeat(
        self,
        buoy_id: str,
        device_id: str,
        sensor_channel: str,
        timestamp_seconds: float,
    ) -> None:
        ...

    def record_buoy_heartbeat(self, buoy_id: str, timestamp_seconds: float) -> None:
        ...
