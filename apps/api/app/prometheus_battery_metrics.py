"""Prometheus adapter for battery telemetry and health metrics."""

from datetime import datetime

from .application.battery_ports import BatteryMetrics
from .metrics import (
    battery_delta_percent,
    battery_device_percent,
    battery_percent,
    buoy_last_seen_timestamp_seconds,
    device_last_seen_timestamp_seconds,
)


class PrometheusBatteryMetrics(BatteryMetrics):
    """Publish battery values and update their buoy/device heartbeat signals."""

    def record_reading(
        self,
        buoy_id: str,
        battery_percent_value: float,
        physical_device_id: str | None,
        sensor_channel: str,
        received_at: datetime,
    ) -> None:
        battery_percent.labels(buoy_id=buoy_id).set(battery_percent_value)
        if physical_device_id is not None:
            device_last_seen_timestamp_seconds.labels(
                buoy_id=buoy_id,
                device_id=physical_device_id,
                sensor_channel=sensor_channel,
            ).set(received_at.timestamp())
        buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(
            received_at.timestamp()
        )

    def record_health(
        self,
        buoy_id: str,
        device_a_percent: float | None,
        device_b_percent: float | None,
        delta_percent: float | None,
    ) -> None:
        for device_id, percentage in (
            ("A", device_a_percent),
            ("B", device_b_percent),
        ):
            if percentage is not None:
                battery_device_percent.labels(
                    buoy_id=buoy_id, device_id=device_id
                ).set(percentage)
        if delta_percent is not None:
            battery_delta_percent.labels(buoy_id=buoy_id).set(delta_percent)
