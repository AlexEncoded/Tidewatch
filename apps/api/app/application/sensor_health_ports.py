"""Application ports for redundant-sensor health evaluation and history."""

from typing import Protocol, runtime_checkable
from collections.abc import Mapping

from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.ambient_light import AmbientLightTelemetrySnapshot
from ..domain.sensor_health import SensorHealthCheckSnapshot, SensorHealthSnapshot
from ..domain.imu import ImuTelemetrySnapshot
from ..domain.underwater_acoustic import UnderwaterAcousticTelemetrySnapshot
from ..domain.acoustic_altimeter import AcousticAltimeterTelemetrySnapshot
from ..domain.atmospheric_pressure import AtmosphericPressureTelemetrySnapshot
from ..domain.air_temperature import AirTemperatureTelemetrySnapshot
from ..domain.humidity import HumidityTelemetrySnapshot
from ..domain.rainfall import RainfallTelemetrySnapshot
from ..domain.chlorophyll_a import ChlorophyllATelemetrySnapshot
from ..domain.conductivity import ConductivityTelemetrySnapshot
from ..domain.ph import PHTelemetrySnapshot
from ..domain.dissolved_oxygen import DissolvedOxygenTelemetrySnapshot
from ..domain.turbidity import TurbidityTelemetrySnapshot
from ..domain.salinity import SalinityTelemetrySnapshot
from ..domain.marine_current import MarineCurrentTelemetrySnapshot
from ..domain.wind import WindTelemetrySnapshot

from ..domain.temperature import TemperatureTelemetrySnapshot


class SensorHealthMetrics(Protocol):
    """Publish channel completeness and redundant sensor decisions."""

    def record_evaluation(
        self,
        buoy_id: str,
        readings: Mapping[str, Mapping[str, object | None]],
        degraded_sensors: list[str],
        missing_sensors: list[str],
        decisions: Mapping[str, str],
    ) -> None:
        ...


@runtime_checkable
class SensorHealthReader(Protocol):
    """Read sensor telemetry and persisted redundant-health checks."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckSnapshot]:
        ...

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        ...

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PressureTelemetrySnapshot]:
        ...

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        ...

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        ...

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        ...

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        ...

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        ...

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        ...

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        ...

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PHTelemetrySnapshot]:
        ...

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ConductivityTelemetrySnapshot]:
        ...

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
        ...

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        ...

    def list_humidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[HumidityTelemetrySnapshot]:
        ...

    def list_air_temperature(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AirTemperatureTelemetrySnapshot]:
        ...

    def list_atmospheric_pressure(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AtmosphericPressureTelemetrySnapshot]:
        ...

    def list_acoustic_altimeter(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AcousticAltimeterTelemetrySnapshot]:
        ...

    def list_underwater_acoustic(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[UnderwaterAcousticTelemetrySnapshot]:
        ...


class SensorHealthCheckGateway(SensorHealthReader, Protocol):
    """Read health inputs and persist completed health evaluations."""

    def add_sensor_health_check(
        self, health: SensorHealthSnapshot
    ) -> SensorHealthCheckSnapshot:
        ...


@runtime_checkable
class SensorHealthCheckWriter(Protocol):
    """Persist a completed sensor-health evaluation."""

    def add_sensor_health_check(
        self, health: SensorHealthSnapshot
    ) -> SensorHealthCheckSnapshot:
        ...
