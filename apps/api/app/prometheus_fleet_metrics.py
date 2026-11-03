"""Prometheus adapter for fleet heartbeat and movement metrics."""

from datetime import datetime

from .application.fleet_ports import FleetMetrics
from .application.system_ports import AvailabilityMetrics
from .metrics import (
    buoy_last_seen_timestamp_seconds,
    buoy_movement_speed_mps,
    device_last_seen_timestamp_seconds,
)


class PrometheusFleetMetrics(FleetMetrics, AvailabilityMetrics):
    """Publish buoy and device liveness and buoy movement signals."""

    def record_buoy_heartbeat(
        self, buoy_id: str, last_seen_at: datetime | None
    ) -> None:
        self.restore_buoy_heartbeat(
            buoy_id,
            last_seen_at.timestamp() if last_seen_at is not None else 0
        )

    def record_device_heartbeat(
        self,
        buoy_id: str,
        device_id: str,
        sensor_channel: str,
        last_seen_at: datetime | None,
    ) -> None:
        self.restore_device_heartbeat(
            buoy_id=buoy_id,
            device_id=device_id,
            sensor_channel=sensor_channel,
            timestamp_seconds=last_seen_at.timestamp() if last_seen_at is not None else 0,
        )

    def record_buoy_movement(self, buoy_id: str, speed_mps: float) -> None:
        buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(speed_mps)

    def clear(self) -> None:
        buoy_last_seen_timestamp_seconds.clear()
        device_last_seen_timestamp_seconds.clear()

    def restore_device_heartbeat(
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

    def restore_buoy_heartbeat(self, buoy_id: str, timestamp_seconds: float) -> None:
        buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(
            timestamp_seconds
        )
