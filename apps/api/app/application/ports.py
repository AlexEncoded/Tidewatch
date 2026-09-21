"""Input ports shared by application services."""

from typing import Protocol


class LocationTelemetryReader(Protocol):
    def list_locations(self, buoy_id: str, limit: int) -> list:
        ...


class ImuTelemetryReader(Protocol):
    def list_imu(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list:
        ...


class PressureTelemetryReader(Protocol):
    def list_pressures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list:
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
    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        ...


class TemperatureTelemetryReader(Protocol):
    def list_temperatures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list:
        ...


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


class MaintenanceReader(
    LocationTelemetryReader,
    BatteryTelemetryReader,
    SensorHealthReader,
    Protocol,
):
    """Read-only queries required by the maintenance application service."""
