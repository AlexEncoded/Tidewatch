from datetime import datetime, timezone

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

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
from .schemas.telemetry import (
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
    WindReading,
    WindReadingCreate,
)


class AcousticAltimeterReadingCreate(BaseModel):
    depth_meters: float = Field(ge=0, le=20000)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AcousticAltimeterReading(AcousticAltimeterReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class UnderwaterAcousticReadingCreate(BaseModel):
    echo_intensity_db: float = Field(ge=-200, le=100)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnderwaterAcousticReading(UnderwaterAcousticReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class TelemetryBatchCreate(BaseModel):
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    temperatures: list[TemperatureReadingCreate] = Field(default_factory=list, max_length=100)
    pressures: list[PressureReadingCreate] = Field(default_factory=list, max_length=100)
    salinity: list[SalinityReadingCreate] = Field(default_factory=list, max_length=100)
    imu: list[ImuReadingCreate] = Field(default_factory=list, max_length=100)
    ambient_light: list[AmbientLightReadingCreate] = Field(default_factory=list, max_length=100)
    wind: list[WindReadingCreate] = Field(default_factory=list, max_length=100)
    marine_current: list[MarineCurrentReadingCreate] = Field(default_factory=list, max_length=100)
    turbidity: list[TurbidityReadingCreate] = Field(default_factory=list, max_length=100)
    dissolved_oxygen: list[DissolvedOxygenReadingCreate] = Field(default_factory=list, max_length=100)
    ph: list[PHReadingCreate] = Field(default_factory=list, max_length=100)
    conductivity: list[ConductivityReadingCreate] = Field(default_factory=list, max_length=100)
    chlorophyll_a: list[ChlorophyllAReadingCreate] = Field(default_factory=list, max_length=100)
    rainfall: list[RainfallReadingCreate] = Field(default_factory=list, max_length=100)
    humidity: list[HumidityReadingCreate] = Field(default_factory=list, max_length=100)
    air_temperature: list[AirTemperatureReadingCreate] = Field(default_factory=list, max_length=100)
    atmospheric_pressure: list[AtmosphericPressureReadingCreate] = Field(default_factory=list, max_length=100)
    acoustic_altimeter: list[AcousticAltimeterReadingCreate] = Field(default_factory=list, max_length=100)
    underwater_acoustic: list[UnderwaterAcousticReadingCreate] = Field(default_factory=list, max_length=100)
    battery: list[BatteryReadingCreate] = Field(default_factory=list, max_length=2)
    location: BuoyLocationReadingCreate | None = None

    @field_validator("battery", mode="before")
    @classmethod
    def normalize_battery_payload(cls, value):
        if value is None:
            return []
        return [value] if isinstance(value, dict) else value

    @model_validator(mode="after")
    def must_contain_readings(self) -> "TelemetryBatchCreate":
        if not (
            self.temperatures
            or self.pressures
            or self.salinity
            or self.imu
            or self.ambient_light
            or self.wind
            or self.marine_current
            or self.turbidity
            or self.dissolved_oxygen
            or self.ph
            or self.conductivity
            or self.chlorophyll_a
            or self.rainfall
            or self.humidity
            or self.air_temperature
            or self.atmospheric_pressure
            or self.acoustic_altimeter
            or self.underwater_acoustic
            or self.battery
            or self.location
        ):
            raise ValueError("Telemetry batch must contain at least one reading")
        battery_devices = [reading.device_id for reading in self.battery]
        if len(battery_devices) != len(set(battery_devices)):
            raise ValueError("Telemetry batch cannot contain duplicate battery devices")
        for family, readings in (
            ("temperature", self.temperatures),
            ("pressure", self.pressures),
            ("salinity", self.salinity),
            ("imu", self.imu),
            ("ambient_light", self.ambient_light),
            ("wind", self.wind),
            ("marine_current", self.marine_current),
            ("turbidity", self.turbidity),
            ("dissolved_oxygen", self.dissolved_oxygen),
            ("ph", self.ph),
            ("conductivity", self.conductivity),
            ("chlorophyll_a", self.chlorophyll_a),
            ("rainfall", self.rainfall),
            ("humidity", self.humidity),
            ("air_temperature", self.air_temperature),
            ("atmospheric_pressure", self.atmospheric_pressure),
            ("acoustic_altimeter", self.acoustic_altimeter),
            ("underwater_acoustic", self.underwater_acoustic),
        ):
            channels = [reading.sensor_channel for reading in readings]
            if len(channels) != len(set(channels)):
                raise ValueError(f"Telemetry batch cannot contain duplicate {family} channels")
        return self


class BuoySummary(BaseModel):
    buoy: Buoy
    latest_temperature: TemperatureReading | None = None
    latest_temperature_a: TemperatureReading | None = None
    latest_temperature_b: TemperatureReading | None = None
    latest_pressure: PressureReading | None = None
    latest_pressure_a: PressureReading | None = None
    latest_pressure_b: PressureReading | None = None
    latest_salinity: SalinityReading | None = None
    latest_salinity_a: SalinityReading | None = None
    latest_salinity_b: SalinityReading | None = None
    latest_imu: ImuReading | None = None
    latest_imu_a: ImuReading | None = None
    latest_imu_b: ImuReading | None = None
    latest_ambient_light: AmbientLightReading | None = None
    latest_ambient_light_a: AmbientLightReading | None = None
    latest_ambient_light_b: AmbientLightReading | None = None
    latest_wind: WindReading | None = None
    latest_wind_a: WindReading | None = None
    latest_wind_b: WindReading | None = None
    latest_marine_current: MarineCurrentReading | None = None
    latest_marine_current_a: MarineCurrentReading | None = None
    latest_marine_current_b: MarineCurrentReading | None = None
    latest_turbidity: TurbidityReading | None = None
    latest_turbidity_a: TurbidityReading | None = None
    latest_turbidity_b: TurbidityReading | None = None
    latest_dissolved_oxygen: DissolvedOxygenReading | None = None
    latest_dissolved_oxygen_a: DissolvedOxygenReading | None = None
    latest_dissolved_oxygen_b: DissolvedOxygenReading | None = None
    latest_ph: PHReading | None = None
    latest_ph_a: PHReading | None = None
    latest_ph_b: PHReading | None = None
    latest_conductivity: ConductivityReading | None = None
    latest_conductivity_a: ConductivityReading | None = None
    latest_conductivity_b: ConductivityReading | None = None
    latest_chlorophyll_a: ChlorophyllAReading | None = None
    latest_chlorophyll_a_a: ChlorophyllAReading | None = None
    latest_chlorophyll_a_b: ChlorophyllAReading | None = None
    latest_rainfall: RainfallReading | None = None
    latest_rainfall_a: RainfallReading | None = None
    latest_rainfall_b: RainfallReading | None = None
    latest_humidity: HumidityReading | None = None
    latest_humidity_a: HumidityReading | None = None
    latest_humidity_b: HumidityReading | None = None
    latest_air_temperature: AirTemperatureReading | None = None
    latest_air_temperature_a: AirTemperatureReading | None = None
    latest_air_temperature_b: AirTemperatureReading | None = None
    latest_atmospheric_pressure: AtmosphericPressureReading | None = None
    latest_atmospheric_pressure_a: AtmosphericPressureReading | None = None
    latest_atmospheric_pressure_b: AtmosphericPressureReading | None = None
    latest_battery: BatteryReading | None = None
    latest_battery_a: BatteryReading | None = None
    latest_battery_b: BatteryReading | None = None
