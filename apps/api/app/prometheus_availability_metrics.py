"""Prometheus adapter for restoring startup availability gauges."""

from .application.system_ports import AvailabilityMetrics
from .metrics import buoy_last_seen_timestamp_seconds, device_last_seen_timestamp_seconds


class PrometheusAvailabilityMetrics(AvailabilityMetrics):
    """Clear and repopulate buoy and device heartbeat gauges."""

    def clear(self) -> None:
        buoy_last_seen_timestamp_seconds.clear()
        device_last_seen_timestamp_seconds.clear()

    def record_device_heartbeat(
        self,
        buoy_id: str,
        device_id: str,
        sensor_channel: str,
        timestamp_seconds: float,
    ) -> None:
        device_last_seen_timestamp_seconds.labels(
            buoy_id=buoy_id,
            device_id=device_id,
            sensor_channel=sensor_channel,
        ).set(timestamp_seconds)

    def record_buoy_heartbeat(self, buoy_id: str, timestamp_seconds: float) -> None:
        buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(
            timestamp_seconds
        )
