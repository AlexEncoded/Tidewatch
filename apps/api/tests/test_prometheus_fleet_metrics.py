from datetime import datetime, timezone

from app.metrics import (
    buoy_last_seen_timestamp_seconds,
    buoy_movement_speed_mps,
    device_last_seen_timestamp_seconds,
)
from app.prometheus_fleet_metrics import PrometheusFleetMetrics


def test_prometheus_fleet_metrics_publish_heartbeats_and_movement() -> None:
    metrics = PrometheusFleetMetrics()
    buoy_id = "fleet-metrics-test-buoy"
    device_id = "fleet-metrics-test-device"
    seen_at = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)

    try:
        metrics.record_buoy_heartbeat(buoy_id, seen_at)
        metrics.record_buoy_heartbeat("fleet-metrics-empty-buoy", None)
        metrics.record_device_heartbeat(buoy_id, device_id, "A", seen_at)
        metrics.record_buoy_movement(buoy_id, 1.25)

        assert buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id)._value.get() == seen_at.timestamp()
        assert buoy_last_seen_timestamp_seconds.labels(
            buoy_id="fleet-metrics-empty-buoy"
        )._value.get() == 0
        assert device_last_seen_timestamp_seconds.labels(
            buoy_id=buoy_id, device_id=device_id, sensor_channel="A"
        )._value.get() == seen_at.timestamp()
        assert buoy_movement_speed_mps.labels(buoy_id=buoy_id)._value.get() == 1.25
    finally:
        buoy_last_seen_timestamp_seconds.remove(buoy_id)
        buoy_last_seen_timestamp_seconds.remove("fleet-metrics-empty-buoy")
        device_last_seen_timestamp_seconds.remove(buoy_id, device_id, "A")
        buoy_movement_speed_mps.remove(buoy_id)
