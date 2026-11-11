"""Application port for ambient-light telemetry."""

from typing import Protocol

from ..domain.ambient_light import AmbientLightTelemetrySnapshot
from ..domain.devices import SensorChannel


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
