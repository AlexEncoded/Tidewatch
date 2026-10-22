"""Input ports shared by application services."""

from typing import Protocol, runtime_checkable
from datetime import datetime

from ..domain.telemetry import (
    LocationTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    AmbientLightTelemetrySnapshot,
    WindTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
)
from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.telemetry import ImuTelemetrySnapshot
from ..domain.temperature import TemperatureTelemetrySnapshot
from ..domain.buoy import BuoyIdentitySnapshot, BuoySnapshot
from ..domain.temperature_alert import TemperatureAlertSnapshot, TemperatureAnomalySnapshot
from ..domain.devices import DeviceSnapshot
from .telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionJobStore,
    TelemetryMetric,
    TelemetryMetrics,
    TelemetryMetricSample,
    TelemetryQueueMetricsReader,
)
from .fleet_ports import (
    BuoyLocationHistoryReader,
    BuoyLocationUpdater,
    BuoyRegistrar,
    BuoyStatusRegistry,
    BuoySummaryReader,
    FleetLocationReader,
    LocationTelemetryReader,
    MovementAnalysisReader,
    StaleBuoyReader,
)
from .sensor_ports import (
    AcousticAltimeterTelemetryGateway,
    AirTemperatureTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
    BatteryTelemetryReader,
    ChlorophyllATelemetryGateway,
    ConductivityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    ImuTelemetryGateway,
    ImuTelemetryReader,
    HumidityTelemetryGateway,
    PHTelemetryGateway,
    AmbientLightTelemetryGateway,
    MarineCurrentTelemetryGateway,
    PressureTelemetryGateway,
    PressureTelemetryReader,
    QualitySummaryReader,
    RainfallTelemetryGateway,
    SalinityTelemetryGateway,
    SensorHealthCheckGateway,
    SensorHealthReader,
    TemperatureTelemetryGateway,
    TemperatureTelemetryReader,
    TurbidityTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
    WindTelemetryGateway,
)


@runtime_checkable
class DatabaseHealthReader(Protocol):
    """Port for checking whether the primary database can answer queries."""

    def check_database(self) -> None:
        ...


class WaveAnalysisReader(ImuTelemetryReader, LocationTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class PressureAnalysisReader(PressureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


@runtime_checkable
class DeviceHealthReader(Protocol):
    """Read-only port for registered physical devices."""

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        ...

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class TemperatureAnalysisReader(TemperatureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class TemperatureAlertsReader(TemperatureTelemetryReader, Protocol):
    def list_buoy_identities(self) -> list[BuoyIdentitySnapshot]:
        ...


class TemperatureAlertStore(TemperatureAlertsReader, Protocol):
    def find_alert(self, buoy_id: str, measured_at: datetime) -> TemperatureAlertSnapshot | None:
        ...

    def create_alert(
        self,
        alert: TemperatureAnomalySnapshot,
        reading_measured_at: datetime,
    ) -> TemperatureAlertSnapshot:
        ...

    def list_alerts(self, status: str = "open") -> list[TemperatureAlertSnapshot]:
        ...

    def resolve_alert(self, alert_id: int) -> TemperatureAlertSnapshot | None:
        ...


@runtime_checkable
class MaintenanceReader(
    LocationTelemetryReader,
    BatteryTelemetryReader,
    SensorHealthReader,
    DeviceHealthReader,
    Protocol,
):
    """Read-only queries required by the maintenance application service."""

    def list_buoy_snapshots(self) -> list[BuoySnapshot]:
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
