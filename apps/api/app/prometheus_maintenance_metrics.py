"""Prometheus adapter for maintenance evaluation results."""

from .application.maintenance_ports import MaintenanceMetrics
from .domain.battery_health import BatteryHealthSnapshot
from .metrics import (
    battery_delta_percent,
    battery_device_percent,
    buoy_movement_speed_mps,
    redundant_device_missing,
)


class PrometheusMaintenanceMetrics(MaintenanceMetrics):
    """Publish battery redundancy and movement signals from maintenance."""

    def record_evaluation(
        self,
        buoy_id: str,
        battery_health: BatteryHealthSnapshot,
        average_speed_mps: float | None,
    ) -> None:
        available_devices = []
        for device_id, percentage in (
            ("A", battery_health.device_a_percent),
            ("B", battery_health.device_b_percent),
        ):
            if percentage is not None:
                battery_device_percent.labels(
                    buoy_id=buoy_id, device_id=device_id
                ).set(percentage)
                available_devices.append(device_id)
        if battery_health.delta_percent is not None:
            battery_delta_percent.labels(buoy_id=buoy_id).set(
                battery_health.delta_percent
            )
        for device_id in ("A", "B"):
            redundant_device_missing.labels(
                buoy_id=buoy_id, device_id=device_id
            ).set(0 if device_id in available_devices else 1)
        if average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(average_speed_mps)
