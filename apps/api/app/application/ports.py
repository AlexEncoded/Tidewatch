"""Input ports shared by application services."""

from typing import Protocol, runtime_checkable
from datetime import datetime

from ..domain.telemetry import LocationTelemetrySnapshot
from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.telemetry import ImuTelemetrySnapshot
from ..domain.temperature import TemperatureTelemetrySnapshot
from ..domain.buoy import (
    BuoyActivitySnapshot,
    BuoyIdentitySnapshot,
    BuoySnapshot,
    BuoyStatusCommand,
    BuoyLocationCommand,
)
from ..domain.temperature_alert import TemperatureAlertSnapshot, TemperatureAnomalySnapshot


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


class ImuTelemetryReader(Protocol):
    def list_imu(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list[ImuTelemetrySnapshot]:
        ...


class WaveAnalysisReader(ImuTelemetryReader, LocationTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class PressureTelemetryReader(Protocol):
    def list_pressures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list[PressureTelemetrySnapshot]:
        ...


class PressureAnalysisReader(PressureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class BatteryTelemetryReader(Protocol):
    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
    ) -> list:
        ...

    def latest_battery(self, buoy_id: str, device_id: str | None = None):
        ...


class QualitySummaryReader(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        ...


@runtime_checkable
class DeviceHealthReader(Protocol):
    """Read-only port for registered physical devices."""

    def list_devices(self, buoy_id: str) -> list:
        ...

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class TemperatureTelemetryReader(Protocol):
    def list_temperatures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list[TemperatureTelemetrySnapshot]:
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
class SensorHealthReader(Protocol):
    """Read-only port for the redundant sensor-health snapshot."""

    def list_temperatures(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_pressures(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_salinity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_imu(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_ambient_light(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_wind(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_marine_current(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_turbidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_dissolved_oxygen(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_ph(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_conductivity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_chlorophyll_a(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_rainfall(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
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

    def list_buoys(self) -> list:
        ...
