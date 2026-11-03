"""Prometheus adapter for redundant sensor-health metrics."""

from collections.abc import Mapping

from .application.sensor_health_ports import SensorHealthMetrics
from .metrics import sensor_channel_missing, sensor_degraded, sensor_health_decision


class PrometheusSensorHealthMetrics(SensorHealthMetrics):
    """Publish channel completeness and selected redundancy decisions."""

    def record_evaluation(
        self,
        buoy_id: str,
        readings: Mapping[str, Mapping[str, object | None]],
        degraded_sensors: list[str],
        missing_sensors: list[str],
        decisions: Mapping[str, str],
    ) -> None:
        for sensor, channels in readings.items():
            has_reading = any(channels.values())
            for channel, reading in channels.items():
                sensor_channel_missing.labels(
                    buoy_id=buoy_id, sensor=sensor, sensor_channel=channel
                ).set(1 if has_reading and not reading else 0)
            sensor_degraded.labels(buoy_id=buoy_id, sensor=sensor).set(
                1
                if sensor in degraded_sensors
                or any(missing.startswith(f"{sensor}:") for missing in missing_sensors)
                else 0
            )

        for sensor in readings:
            for decision in ("average", "fallback_a", "fallback_b", "invalid"):
                sensor_health_decision.labels(
                    buoy_id=buoy_id, sensor=sensor, decision=decision
                ).set(1 if decisions[sensor] == decision else 0)
