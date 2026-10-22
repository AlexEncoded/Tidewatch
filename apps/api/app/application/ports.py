"""Input ports shared by application services."""

from typing import Protocol, runtime_checkable
from .telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionJobStore,
    TelemetryMetric,
    TelemetryMetrics,
    TelemetryMetricSample,
    TelemetryQueueMetricsReader,
    TelemetryIngestionGateway,
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
from .device_ports import (
    DeviceHealthReader,
    DeviceListingReader,
    DeviceRegistry,
    DeviceStatusRegistry,
)
from .maintenance_ports import MaintenanceReader
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
    PressureAnalysisReader,
    QualitySummaryReader,
    RainfallTelemetryGateway,
    SalinityTelemetryGateway,
    SensorHealthCheckGateway,
    SensorHealthReader,
    TemperatureTelemetryGateway,
    TemperatureTelemetryReader,
    TemperatureAnalysisReader,
    TemperatureAlertsReader,
    TemperatureAlertStore,
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
    """Compose sensor and fleet reads required by wave analysis."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


# This cross-context protocol remains re-exported here for compatibility.
