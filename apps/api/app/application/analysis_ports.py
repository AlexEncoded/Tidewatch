"""Composite input ports for cross-context analysis use cases."""

from typing import Protocol

from .fleet_ports import LocationTelemetryReader
from .sensor_ports import (
    ImuTelemetryReader,
    PressureTelemetryReader,
    TemperatureTelemetryReader,
)


class PressureAnalysisReader(PressureTelemetryReader, Protocol):
    """Read pressure telemetry required by sea-state analysis."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class TemperatureAnalysisReader(TemperatureTelemetryReader, Protocol):
    """Read temperature telemetry required by temperature analysis."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class WaveAnalysisReader(ImuTelemetryReader, LocationTelemetryReader, Protocol):
    """Compose sensor and fleet reads required by wave analysis."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...
