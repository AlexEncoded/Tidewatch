"""Application ports for core marine-water telemetry."""

from typing import Protocol

from ..domain.devices import SensorChannel
from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.salinity import SalinityTelemetrySnapshot
from ..domain.temperature import TemperatureTelemetrySnapshot


class TemperatureTelemetryReader(Protocol):
    def list_temperatures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: SensorChannel | None = "A",
    ) -> list[TemperatureTelemetrySnapshot]:
        ...


class TemperatureTelemetryGateway(TemperatureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_temperature(
        self, reading: TemperatureTelemetrySnapshot
    ) -> TemperatureTelemetrySnapshot:
        ...


class PressureTelemetryReader(Protocol):
    def list_pressures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: SensorChannel | None = "A",
    ) -> list[PressureTelemetrySnapshot]:
        ...


class PressureTelemetryGateway(PressureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_pressure(
        self, reading: PressureTelemetrySnapshot
    ) -> PressureTelemetrySnapshot:
        ...


class SalinityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_salinity(
        self, reading: SalinityTelemetrySnapshot
    ) -> SalinityTelemetrySnapshot:
        ...

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        ...
