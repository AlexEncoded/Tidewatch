"""Application ports for redundant-sensor health evaluation and history."""

from typing import Protocol, runtime_checkable
from collections.abc import Mapping

from ..domain.fleet.devices import SensorChannel
from ..domain.sensors.sensor_family import SensorFamily
from ..domain.sensors.reading_quality import MeasuredReading
from ..domain.sensors.pressure import PressureTelemetrySnapshot
from ..domain.sensors.ambient_light import AmbientLightTelemetrySnapshot
from ..domain.sensors.sensor_health import (
    ChannelDecision,
    SensorHealthCheckSnapshot,
    SensorHealthSnapshot,
)
from ..domain.sensors.sensor_health_rules import DegradedSensorName
from ..domain.sensors.imu import ImuTelemetrySnapshot
from ..domain.sensors.underwater_acoustic import UnderwaterAcousticTelemetrySnapshot
from ..domain.sensors.acoustic_altimeter import AcousticAltimeterTelemetrySnapshot
from ..domain.sensors.atmospheric_pressure import AtmosphericPressureTelemetrySnapshot
from ..domain.sensors.air_temperature import AirTemperatureTelemetrySnapshot
from ..domain.sensors.humidity import HumidityTelemetrySnapshot
from ..domain.sensors.rainfall import RainfallTelemetrySnapshot
from ..domain.sensors.chlorophyll_a import ChlorophyllATelemetrySnapshot
from ..domain.sensors.conductivity import ConductivityTelemetrySnapshot
from ..domain.sensors.ph import PHTelemetrySnapshot
from ..domain.sensors.dissolved_oxygen import DissolvedOxygenTelemetrySnapshot
from ..domain.sensors.turbidity import TurbidityTelemetrySnapshot
from ..domain.sensors.salinity import SalinityTelemetrySnapshot
from ..domain.sensors.marine_current import MarineCurrentTelemetrySnapshot
from ..domain.sensors.wind import WindTelemetrySnapshot

from ..domain.sensors.temperature import TemperatureTelemetrySnapshot


class SensorHealthMetrics(Protocol):
    """Publish channel completeness and redundant sensor decisions."""

    def record_evaluation(
        self,
        buoy_id: str,
        readings: Mapping[SensorFamily, Mapping[SensorChannel, MeasuredReading | None]],
        degraded_sensors: list[DegradedSensorName],
        missing_sensors: list[str],
        decisions: Mapping[SensorFamily, ChannelDecision],
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
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        ...

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[PressureTelemetrySnapshot]:
        ...

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        ...

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        ...

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        ...

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        ...

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        ...

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        ...

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        ...

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[PHTelemetrySnapshot]:
        ...

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ConductivityTelemetrySnapshot]:
        ...

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
        ...

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        ...

    def list_humidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[HumidityTelemetrySnapshot]:
        ...

    def list_air_temperature(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AirTemperatureTelemetrySnapshot]:
        ...

    def list_atmospheric_pressure(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AtmosphericPressureTelemetrySnapshot]:
        ...

    def list_acoustic_altimeter(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AcousticAltimeterTelemetrySnapshot]:
        ...

    def list_underwater_acoustic(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
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
