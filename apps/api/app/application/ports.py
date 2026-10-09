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
from ..domain.buoy import (
    BuoyActivitySnapshot,
    BuoyIdentitySnapshot,
    BuoySnapshot,
    BuoySummarySnapshot,
    BuoyStatusCommand,
    BuoyLocationCommand,
)
from ..domain.temperature_alert import TemperatureAlertSnapshot, TemperatureAnomalySnapshot
from ..domain.sensor_health import SensorHealthCheckSnapshot, SensorHealthSnapshot


class FleetLocationReader(Protocol):
    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        ...


@runtime_checkable
class DatabaseHealthReader(Protocol):
    """Port for checking whether the primary database can answer queries."""

    def check_database(self) -> None:
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


class ImuTelemetryReader(Protocol):
    def list_imu(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list[ImuTelemetrySnapshot]:
        ...


class ImuTelemetryGateway(ImuTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_imu(self, reading: ImuTelemetrySnapshot) -> ImuTelemetrySnapshot:
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


class PressureTelemetryGateway(PressureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_pressure(
        self, reading: PressureTelemetrySnapshot
    ) -> PressureTelemetrySnapshot:
        ...


class SalinityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_salinity(
        self, reading: SalinityTelemetrySnapshot
    ) -> SalinityTelemetrySnapshot:
        ...

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        ...


class AmbientLightTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_ambient_light(
        self, reading: AmbientLightTelemetrySnapshot
    ) -> AmbientLightTelemetrySnapshot:
        ...

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        ...


class WindTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_wind(self, reading: WindTelemetrySnapshot) -> WindTelemetrySnapshot:
        ...

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        ...


class MarineCurrentTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_marine_current(
        self, reading: MarineCurrentTelemetrySnapshot
    ) -> MarineCurrentTelemetrySnapshot:
        ...

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        ...


class TurbidityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_turbidity(
        self, reading: TurbidityTelemetrySnapshot
    ) -> TurbidityTelemetrySnapshot:
        ...

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        ...


class DissolvedOxygenTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_dissolved_oxygen(
        self, reading: DissolvedOxygenTelemetrySnapshot
    ) -> DissolvedOxygenTelemetrySnapshot:
        ...

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        ...


class PHTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_ph(self, reading: PHTelemetrySnapshot) -> PHTelemetrySnapshot:
        ...

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
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
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
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
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
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

    def get_device(self, device_id: str):
        ...

    def mark_device_seen(self, device, seen_at: datetime):
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


class TemperatureTelemetryGateway(TemperatureTelemetryReader, Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_temperature(
        self, reading: TemperatureTelemetrySnapshot
    ) -> TemperatureTelemetrySnapshot:
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

    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckSnapshot]:
        ...

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


class SensorHealthCheckGateway(SensorHealthReader, Protocol):
    """Read sensor inputs and persist the resulting health evaluation."""

    def add_sensor_health_check(
        self, health: SensorHealthSnapshot
    ) -> SensorHealthCheckSnapshot:
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

    def get_device(self, device_id: str):
        ...

    def mark_device_seen(self, device, seen_at: datetime):
        ...
