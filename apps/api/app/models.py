from .schemas.fleet import (
    Buoy,
    BuoyCreate,
    BuoyHealth,
    BuoyLocationReading,
    BuoyLocationReadingCreate,
    BuoyLocationUpdate,
    BuoyStatusUpdate,
)
from .schemas.battery import (
    BatteryAnalysis,
    BatteryHealth,
    BatteryReading,
    BatteryReadingCreate,
)
from .schemas.analytics import (
    MovementAnalysis,
    PressureAnalysis,
    StoredTemperatureAlert,
    TemperatureAlert,
    TemperatureAnalysis,
    WaveAnalysis,
)
from .schemas.quality import QualitySummary
from .schemas.sensors import SensorHealth, SensorHealthCheck
from .schemas.maintenance import MaintenanceIssue, MaintenanceNotificationResult
from .schemas.ingestion import TelemetryBatchCreate
from .schemas.fleet_summary import BuoySummary
from .schemas.telemetry import (
    AcousticAltimeterReading,
    AcousticAltimeterReadingCreate,
    AirTemperatureReading,
    AirTemperatureReadingCreate,
    AtmosphericPressureReading,
    AtmosphericPressureReadingCreate,
    ChlorophyllAReading,
    ChlorophyllAReadingCreate,
    PressureReading,
    PressureReadingCreate,
    SalinityReading,
    SalinityReadingCreate,
    AmbientLightReading,
    AmbientLightReadingCreate,
    ConductivityReading,
    ConductivityReadingCreate,
    DissolvedOxygenReading,
    DissolvedOxygenReadingCreate,
    ImuReading,
    ImuReadingCreate,
    HumidityReading,
    HumidityReadingCreate,
    MarineCurrentReading,
    MarineCurrentReadingCreate,
    PHReading,
    PHReadingCreate,
    RainfallReading,
    RainfallReadingCreate,
    TelemetryIngestResponse,
    TemperatureReading,
    TemperatureReadingCreate,
    TurbidityReading,
    TurbidityReadingCreate,
    UnderwaterAcousticReading,
    UnderwaterAcousticReadingCreate,
    WindReading,
    WindReadingCreate,
)
