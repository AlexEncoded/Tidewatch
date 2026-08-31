"""Input ports shared by application services."""

from typing import Protocol


class LocationTelemetryReader(Protocol):
    def list_locations(self, buoy_id: str, limit: int) -> list:
        ...


class ImuTelemetryReader(Protocol):
    def list_imu(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...


class PressureTelemetryReader(Protocol):
    def list_pressures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list:
        ...


class BatteryTelemetryReader(Protocol):
    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
    ) -> list:
        ...

    def latest_battery(self, buoy_id: str, device_id: str | None = None):
        ...


class TemperatureTelemetryReader(Protocol):
    def list_temperatures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list:
        ...
