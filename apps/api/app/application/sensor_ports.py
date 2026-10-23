"""Application ports for sensor diagnostics and health persistence."""

from typing import Protocol

from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.telemetry import (
    AcousticAltimeterTelemetrySnapshot,
    AirTemperatureTelemetrySnapshot,
    AmbientLightTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    ImuTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    RainfallTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
    WindTelemetrySnapshot,
)
from ..domain.temperature import TemperatureTelemetrySnapshot


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

    def add_turbidity(self, reading: TurbidityTelemetrySnapshot) -> TurbidityTelemetrySnapshot:
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

    def add_rainfall(self, reading: RainfallTelemetrySnapshot) -> RainfallTelemetrySnapshot:
        ...

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        ...


class HumidityTelemetryGateway(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def add_humidity(self, reading: HumidityTelemetrySnapshot) -> HumidityTelemetrySnapshot:
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
