from datetime import datetime, timezone

from app.metrics import (
    battery_delta_percent,
    battery_device_percent,
    battery_percent,
    buoy_last_seen_timestamp_seconds,
    device_last_seen_timestamp_seconds,
)
from app.prometheus_battery_metrics import PrometheusBatteryMetrics


def test_prometheus_battery_metrics_publish_reading_heartbeats_and_health() -> None:
    metrics = PrometheusBatteryMetrics()
    buoy_id = "battery-metrics-test-buoy"
    physical_device_id = "battery-metrics-test-device"
    received_at = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
    labeled_metrics = (
        (battery_percent, (buoy_id,)),
        (buoy_last_seen_timestamp_seconds, (buoy_id,)),
        (device_last_seen_timestamp_seconds, (buoy_id, physical_device_id, "A")),
        (battery_device_percent, (buoy_id, "A")),
        (battery_delta_percent, (buoy_id,)),
    )
    old_values = {}
    for metric, labels in labeled_metrics:
        sample = metric.labels(*labels)
        try:
            old_values[(metric, labels)] = sample._value.get()
        except AttributeError:
            old_values[(metric, labels)] = None

    try:
        metrics.record_reading(
            buoy_id, 87.5, physical_device_id, "A", received_at
        )
        metrics.record_health(buoy_id, 87.5, 80.0, 7.5)

        assert battery_percent.labels(buoy_id=buoy_id)._value.get() == 87.5
        assert buoy_last_seen_timestamp_seconds.labels(
            buoy_id=buoy_id
        )._value.get() == received_at.timestamp()
        assert device_last_seen_timestamp_seconds.labels(
            buoy_id=buoy_id,
            device_id=physical_device_id,
            sensor_channel="A",
        )._value.get() == received_at.timestamp()
        assert battery_device_percent.labels(
            buoy_id=buoy_id, device_id="A"
        )._value.get() == 87.5
        assert battery_device_percent.labels(
            buoy_id=buoy_id, device_id="B"
        )._value.get() == 80.0
        assert battery_delta_percent.labels(buoy_id=buoy_id)._value.get() == 7.5
    finally:
        for (metric, labels), value in old_values.items():
            if value is None:
                metric.remove(*labels)
            else:
                metric.labels(*labels).set(value)
        battery_device_percent.remove(buoy_id, "B")
