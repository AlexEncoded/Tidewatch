"""Backward-compatible facade for context-specific application ports."""

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
from .analysis_ports import WaveAnalysisReader
from .battery_ports import BatteryTelemetryReader
from .sensor_ports import (
    AcousticAltimeterTelemetryGateway,
    AirTemperatureTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
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
from .system_ports import DatabaseHealthReader
