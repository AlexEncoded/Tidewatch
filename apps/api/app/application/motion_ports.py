"""Application ports for inertial-motion telemetry."""

from typing import Protocol

from ..domain.devices import SensorChannel
from ..domain.imu import ImuTelemetrySnapshot


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
