"""Application ports for acoustic telemetry."""

from typing import Protocol

from ..domain.acoustic_altimeter import AcousticAltimeterTelemetrySnapshot
from ..domain.devices import SensorChannel
from ..domain.underwater_acoustic import UnderwaterAcousticTelemetrySnapshot


class AcousticAltimeterTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_acoustic_altimeter(
        self, reading: AcousticAltimeterTelemetrySnapshot
    ) -> AcousticAltimeterTelemetrySnapshot:
        ...

    def list_acoustic_altimeter(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AcousticAltimeterTelemetrySnapshot]:
        ...


class UnderwaterAcousticTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_underwater_acoustic(
        self, reading: UnderwaterAcousticTelemetrySnapshot
    ) -> UnderwaterAcousticTelemetrySnapshot:
        ...

    def list_underwater_acoustic(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[UnderwaterAcousticTelemetrySnapshot]:
        ...
