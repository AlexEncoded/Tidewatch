from app.metrics import (
    sensor_channel_missing,
    sensor_degraded,
    sensor_health_decision,
)
from app.prometheus_sensor_health_metrics import PrometheusSensorHealthMetrics


def test_prometheus_sensor_health_metrics_publish_missing_and_decisions() -> None:
    metrics = PrometheusSensorHealthMetrics()
    buoy_id = "sensor-health-metrics-test-buoy"
    label_values = {
        (sensor_channel_missing, (buoy_id, "temperature", "A")),
        (sensor_channel_missing, (buoy_id, "temperature", "B")),
        (sensor_degraded, (buoy_id, "temperature")),
        *(
            (sensor_health_decision, (buoy_id, "temperature", decision))
            for decision in ("average", "fallback_a", "fallback_b", "invalid")
        ),
    }
    old_values = {}
    for metric, labels in label_values:
        sample = metric.labels(*labels)
        try:
            old_values[(metric, labels)] = sample._value.get()
        except AttributeError:
            old_values[(metric, labels)] = None

    try:
        metrics.record_evaluation(
            buoy_id,
            {"temperature": {"A": object(), "B": None}},
            [],
            ["temperature:B"],
            {"temperature": "fallback_a"},
        )

        assert sensor_channel_missing.labels(
            buoy_id=buoy_id, sensor="temperature", sensor_channel="A"
        )._value.get() == 0
        assert sensor_channel_missing.labels(
            buoy_id=buoy_id, sensor="temperature", sensor_channel="B"
        )._value.get() == 1
        assert sensor_degraded.labels(
            buoy_id=buoy_id, sensor="temperature"
        )._value.get() == 1
        assert sensor_health_decision.labels(
            buoy_id=buoy_id, sensor="temperature", decision="fallback_a"
        )._value.get() == 1
        assert sensor_health_decision.labels(
            buoy_id=buoy_id, sensor="temperature", decision="average"
        )._value.get() == 0
    finally:
        for (metric, labels), value in old_values.items():
            if value is None:
                metric.remove(*labels)
            else:
                metric.labels(*labels).set(value)
