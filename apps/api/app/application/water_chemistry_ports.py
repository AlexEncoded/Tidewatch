"""Application ports for water-chemistry telemetry."""

from typing import Protocol

from ..domain.chlorophyll_a import ChlorophyllATelemetrySnapshot
from ..domain.conductivity import ConductivityTelemetrySnapshot
from ..domain.devices import SensorChannel
from ..domain.dissolved_oxygen import DissolvedOxygenTelemetrySnapshot
from ..domain.ph import PHTelemetrySnapshot


class DissolvedOxygenTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_dissolved_oxygen(
        self, reading: DissolvedOxygenTelemetrySnapshot
    ) -> DissolvedOxygenTelemetrySnapshot:
        ...

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        ...


class PHTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_ph(self, reading: PHTelemetrySnapshot) -> PHTelemetrySnapshot:
        ...

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[PHTelemetrySnapshot]:
        ...


class ConductivityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_conductivity(
        self, reading: ConductivityTelemetrySnapshot
    ) -> ConductivityTelemetrySnapshot:
        ...

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ConductivityTelemetrySnapshot]:
        ...


class ChlorophyllATelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_chlorophyll_a(
        self, reading: ChlorophyllATelemetrySnapshot
    ) -> ChlorophyllATelemetrySnapshot:
        ...

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
        ...
