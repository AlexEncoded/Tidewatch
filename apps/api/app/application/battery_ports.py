"""Application ports for battery telemetry and physical-device presence."""

from datetime import datetime
from typing import Protocol

from ..domain.devices import DeviceSnapshot, SensorChannel
from ..domain.battery import BatteryTelemetrySnapshot


class BatteryTelemetryReader(Protocol):
    """Read and record battery telemetry without exposing its SQL adapter."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        ...

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        ...

    def add_battery(self, reading: BatteryTelemetrySnapshot) -> BatteryTelemetrySnapshot:
        ...

    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> list[BatteryTelemetrySnapshot]:
        ...

    def latest_battery(
        self,
        buoy_id: str,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> BatteryTelemetrySnapshot | None:
        ...


class BatteryMetrics(Protocol):
    """Publish battery readings, associated heartbeats, and health summaries."""

    def record_reading(
        self,
        buoy_id: str,
        battery_percent: float,
        physical_device_id: str | None,
        sensor_channel: SensorChannel,
        received_at: datetime,
    ) -> None:
        ...

    def record_health(
        self,
        buoy_id: str,
        device_a_percent: float | None,
        device_b_percent: float | None,
        delta_percent: float | None,
    ) -> None:
        ...
