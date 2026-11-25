"""Application ports for wind and marine-current flow telemetry."""

from typing import Protocol

from ..domain.fleet.devices import SensorChannel
from ..domain.sensors.marine_current import MarineCurrentTelemetrySnapshot
from ..domain.sensors.wind import WindTelemetrySnapshot


class WindTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_wind(self, reading: WindTelemetrySnapshot) -> WindTelemetrySnapshot:
        ...

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        ...


class MarineCurrentTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_marine_current(
        self, reading: MarineCurrentTelemetrySnapshot
    ) -> MarineCurrentTelemetrySnapshot:
        ...

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        ...
