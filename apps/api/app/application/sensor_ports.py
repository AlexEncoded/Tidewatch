"""Application ports for sensor diagnostics and health persistence."""

from typing import Protocol

from ..domain.devices import SensorChannel

from ..domain.ambient_light import AmbientLightTelemetrySnapshot

from ..domain.imu import ImuTelemetrySnapshot
from ..domain.turbidity import TurbidityTelemetrySnapshot


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


class TurbidityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_turbidity(self, reading: TurbidityTelemetrySnapshot) -> TurbidityTelemetrySnapshot:
        ...

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        ...
