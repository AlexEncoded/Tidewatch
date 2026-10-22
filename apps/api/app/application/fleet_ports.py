"""Application ports for fleet identity, status, and location operations."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from ..domain.buoy import (
    BuoyActivitySnapshot,
    BuoyLocationCommand,
    BuoySnapshot,
    BuoyStatusCommand,
    BuoySummarySnapshot,
)
from ..domain.telemetry import LocationTelemetrySnapshot


class FleetLocationReader(Protocol):
    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        ...


class StaleBuoyReader(Protocol):
    def list_buoy_activity(self) -> list[BuoyActivitySnapshot]:
        ...


class BuoyStatusRegistry(Protocol):
    def update_buoy_status(
        self, buoy_id: str, command: BuoyStatusCommand
    ) -> BuoySnapshot | None:
        ...


class BuoyLocationUpdater(Protocol):
    def update_buoy_location(
        self, buoy_id: str, command: BuoyLocationCommand
    ) -> BuoySnapshot | None:
        ...


class BuoyRegistrar(Protocol):
    def register_buoy(self, buoy: BuoySnapshot) -> BuoySnapshot:
        ...


@runtime_checkable
class BuoySummaryReader(Protocol):
    def list_buoy_summaries(self) -> list[BuoySummarySnapshot]:
        ...


class LocationTelemetryReader(Protocol):
    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        ...


class MovementAnalysisReader(LocationTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class BuoyLocationHistoryReader(LocationTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...
