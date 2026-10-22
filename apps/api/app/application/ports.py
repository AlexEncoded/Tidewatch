"""Input ports shared by application services."""

from typing import Protocol, runtime_checkable
from datetime import datetime

from ..domain.telemetry import (
    BatteryTelemetrySnapshot,
    LocationTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    AmbientLightTelemetrySnapshot,
    WindTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    PHTelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    RainfallTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    AirTemperatureTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    AcousticAltimeterTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
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
    ChlorophyllATelemetryGateway,
    ConductivityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    ImuTelemetryGateway,
    ImuTelemetryReader,
    PHTelemetryGateway,
    AmbientLightTelemetryGateway,
    MarineCurrentTelemetryGateway,
    PressureTelemetryGateway,
    PressureTelemetryReader,
    SalinityTelemetryGateway,
    SensorHealthCheckGateway,
    SensorHealthReader,
    TemperatureTelemetryGateway,
    TemperatureTelemetryReader,
    TurbidityTelemetryGateway,
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


class RainfallTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_rainfall(
        self, reading: RainfallTelemetrySnapshot
    ) -> RainfallTelemetrySnapshot:
        ...

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        ...


class HumidityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_humidity(
        self, reading: HumidityTelemetrySnapshot
    ) -> HumidityTelemetrySnapshot:
        ...

    def list_humidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[HumidityTelemetrySnapshot]:
        ...


class AirTemperatureTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_air_temperature(
        self, reading: AirTemperatureTelemetrySnapshot
    ) -> AirTemperatureTelemetrySnapshot:
        ...

    def list_air_temperature(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AirTemperatureTelemetrySnapshot]:
        ...


class AtmosphericPressureTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_atmospheric_pressure(
        self, reading: AtmosphericPressureTelemetrySnapshot
    ) -> AtmosphericPressureTelemetrySnapshot:
        ...

    def list_atmospheric_pressure(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AtmosphericPressureTelemetrySnapshot]:
        ...


class AcousticAltimeterTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_acoustic_altimeter(
        self, reading: AcousticAltimeterTelemetrySnapshot
    ) -> AcousticAltimeterTelemetrySnapshot:
        ...

    def list_acoustic_altimeter(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
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
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[UnderwaterAcousticTelemetrySnapshot]:
        ...


class PressureAnalysisReader(PressureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class BatteryTelemetryReader(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        ...

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        ...

    def add_battery(self, reading: BatteryTelemetrySnapshot) -> BatteryTelemetrySnapshot:
        ...

    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> list[BatteryTelemetrySnapshot]:
        ...

    def latest_battery(
        self,
        buoy_id: str,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> BatteryTelemetrySnapshot | None:
        ...


class QualitySummaryReader(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
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
