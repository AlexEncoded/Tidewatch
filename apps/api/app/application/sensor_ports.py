"""Application ports for sensor diagnostics and health persistence."""

from typing import Protocol

from ..domain.devices import SensorChannel

from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.ambient_light import AmbientLightTelemetrySnapshot

from ..domain.imu import ImuTelemetrySnapshot
from ..domain.turbidity import TurbidityTelemetrySnapshot
from ..domain.salinity import SalinityTelemetrySnapshot
from ..domain.marine_current import MarineCurrentTelemetrySnapshot
from ..domain.wind import WindTelemetrySnapshot
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


class ImuTelemetryReader(Protocol):
    def list_imu(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: SensorChannel | None = "A",
    ) -> list[ImuTelemetrySnapshot]:
        ...


class ImuTelemetryGateway(ImuTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_imu(self, reading: ImuTelemetrySnapshot) -> ImuTelemetrySnapshot:
        ...


class AmbientLightTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_ambient_light(
        self, reading: AmbientLightTelemetrySnapshot
    ) -> AmbientLightTelemetrySnapshot:
        ...

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        ...


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


class TurbidityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_turbidity(self, reading: TurbidityTelemetrySnapshot) -> TurbidityTelemetrySnapshot:
        ...

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        ...
