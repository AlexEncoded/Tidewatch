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
from .quality_ports import QualitySummaryReader
from .alert_ports import TemperatureAlertsReader, TemperatureAlertStore
from .device_ports import (
    DeviceHealthReader,
    DeviceListingReader,
    DeviceRegistry,
    DeviceStatusRegistry,
)
from .maintenance_ports import MaintenanceReader
from .analysis_ports import (
    PressureAnalysisReader,
    TemperatureAnalysisReader,
    WaveAnalysisReader,
)
from .battery_ports import BatteryTelemetryReader
from .sensor_health_ports import (
    SensorHealthCheckGateway,
    SensorHealthCheckWriter,
    SensorHealthReader,
)
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
    RainfallTelemetryGateway,
    SalinityTelemetryGateway,
    TemperatureTelemetryGateway,
    TemperatureTelemetryReader,
    TurbidityTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
    WindTelemetryGateway,
)
from .system_ports import DatabaseHealthReader
