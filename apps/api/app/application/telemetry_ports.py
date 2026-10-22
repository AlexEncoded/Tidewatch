"""Application ports for telemetry ingestion, queueing, and metrics."""

from datetime import datetime
from typing import Callable, Protocol, TypeVar, runtime_checkable

from ..domain.buoy import BuoySnapshot
from ..domain.devices import DeviceSnapshot
from ..domain.telemetry import LocationTelemetrySnapshot
from ..domain.telemetry_job import TelemetryIngestionJobSnapshot
from .fleet_ports import LocationTelemetryReader
from .sensor_ports import (
    AcousticAltimeterTelemetryGateway,
    AirTemperatureTelemetryGateway,
    AmbientLightTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
    BatteryTelemetryReader,
    ChlorophyllATelemetryGateway,
    ConductivityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    HumidityTelemetryGateway,
    ImuTelemetryGateway,
    MarineCurrentTelemetryGateway,
    PHTelemetryGateway,
    PressureTelemetryGateway,
    RainfallTelemetryGateway,
    SalinityTelemetryGateway,
    TemperatureTelemetryGateway,
    TurbidityTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
    WindTelemetryGateway,
)

T = TypeVar("T")


class TelemetryQueueMetricsReader(Protocol):
    """Read bounded-cardinality durable queue metrics for observability."""

    def observability_snapshot(self) -> dict[str, int | float]:
        ...


@runtime_checkable
class TelemetryIngestionJobStore(Protocol):
    """Enqueue and read durable telemetry jobs without exposing a SQL adapter."""

    def enqueue(
        self,
        buoy_id: str,
        payload: dict,
        now: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> TelemetryIngestionJobSnapshot:
        ...

    def get(self, job_id: str) -> TelemetryIngestionJobSnapshot | None:
        ...


class TelemetryBatchUnitOfWork(Protocol):
    """Run telemetry ingestion and related state changes atomically."""

    def run_atomically(self, action: Callable[[], T]) -> T:
        ...


class TelemetryMetricSample(Protocol):
    """A labeled metric value that can be incremented or replaced."""

    def inc(self, amount: float = 1) -> None:
        ...

    def set(self, value: float) -> None:
        ...


class TelemetryMetric(Protocol):
    """A metric family supporting bounded labels."""

    def labels(self, **labels: str) -> TelemetryMetricSample:
        ...


class TelemetryMetrics(Protocol):
    """Port for recording telemetry counters and gauges."""

    def metric(self, name: str) -> TelemetryMetric:
        ...


@runtime_checkable
class TelemetryIngestionGateway(
    TemperatureTelemetryGateway,
    PressureTelemetryGateway,
    SalinityTelemetryGateway,
    ImuTelemetryGateway,
    AmbientLightTelemetryGateway,
    WindTelemetryGateway,
    MarineCurrentTelemetryGateway,
    TurbidityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    PHTelemetryGateway,
    ConductivityTelemetryGateway,
    ChlorophyllATelemetryGateway,
    RainfallTelemetryGateway,
    HumidityTelemetryGateway,
    AirTemperatureTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
    AcousticAltimeterTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
    BatteryTelemetryReader,
    LocationTelemetryReader,
    Protocol,
):
    """Write batch telemetry and support heartbeat/movement use cases."""

    def add_location(self, reading: LocationTelemetrySnapshot):
        ...

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        ...

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        ...

    def mark_buoy_seen_by_id(
        self, buoy_id: str, seen_at: datetime
    ) -> BuoySnapshot | None:
        ...
