"""Application ports for weather telemetry."""

from typing import Protocol

from ..domain.air_temperature import AirTemperatureTelemetrySnapshot
from ..domain.atmospheric_pressure import AtmosphericPressureTelemetrySnapshot
from ..domain.devices import SensorChannel
from ..domain.humidity import HumidityTelemetrySnapshot
from ..domain.rainfall import RainfallTelemetrySnapshot


class RainfallTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_rainfall(
        self, reading: RainfallTelemetrySnapshot
    ) -> RainfallTelemetrySnapshot:
        ...

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        ...


class HumidityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_humidity(
        self, reading: HumidityTelemetrySnapshot
    ) -> HumidityTelemetrySnapshot:
        ...

    def list_humidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[HumidityTelemetrySnapshot]:
        ...


class AirTemperatureTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_air_temperature(
        self, reading: AirTemperatureTelemetrySnapshot
    ) -> AirTemperatureTelemetrySnapshot:
        ...

    def list_air_temperature(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AirTemperatureTelemetrySnapshot]:
        ...


class AtmosphericPressureTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_atmospheric_pressure(
        self, reading: AtmosphericPressureTelemetrySnapshot
    ) -> AtmosphericPressureTelemetrySnapshot:
        ...

    def list_atmospheric_pressure(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AtmosphericPressureTelemetrySnapshot]:
        ...
