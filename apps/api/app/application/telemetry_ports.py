"""Application ports for telemetry ingestion, queueing, and metrics."""

from datetime import datetime
from typing import Callable, Protocol, TypeVar, runtime_checkable

from ..domain.telemetry_job import TelemetryIngestionJobSnapshot

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
