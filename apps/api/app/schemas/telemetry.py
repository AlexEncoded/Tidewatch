"""HTTP contracts for core sensor telemetry and ingestion responses."""

from datetime import datetime, timezone
from ..domain.telemetry_types import (
    AIR_TEMPERATURE_MAX_CELSIUS,
    AIR_TEMPERATURE_MIN_CELSIUS,
    ATMOSPHERIC_PRESSURE_MAX_KPA,
    ATMOSPHERIC_PRESSURE_MIN_KPA,
    DISSOLVED_OXYGEN_MAX_MG_L,
    DISSOLVED_OXYGEN_MIN_MG_L,
    HUMIDITY_MAX_PERCENT,
    HUMIDITY_MIN_PERCENT,
    PH_MAX,
    PH_MIN,
    ReadingQuality,
    SALINITY_MAX_PSU,
    SALINITY_MIN_PSU,
    SensorChannel,
    TURBIDITY_MAX_NTU,
    TURBIDITY_MIN_NTU,
)
from ..domain.temperature import (
    SEA_TEMPERATURE_MAX_CELSIUS,
    SEA_TEMPERATURE_MIN_CELSIUS,
)
from ..domain.pressure import WATER_PRESSURE_MAX_KPA, WATER_PRESSURE_MIN_KPA

from pydantic import BaseModel, Field


class TemperatureReadingCreate(BaseModel):
    temperature_celsius: float = Field(
        ge=SEA_TEMPERATURE_MIN_CELSIUS,
        le=SEA_TEMPERATURE_MAX_CELSIUS,
    )
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemperatureReading(TemperatureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class PressureReadingCreate(BaseModel):
    pressure_kpa: float = Field(ge=WATER_PRESSURE_MIN_KPA, le=WATER_PRESSURE_MAX_KPA)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PressureReading(PressureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class SalinityReadingCreate(BaseModel):
    salinity_psu: float = Field(ge=SALINITY_MIN_PSU, le=SALINITY_MAX_PSU)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SalinityReading(SalinityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class ImuReadingCreate(BaseModel):
    acceleration_x_mps2: float = Field(ge=-200, le=200)
    acceleration_y_mps2: float = Field(ge=-200, le=200)
    acceleration_z_mps2: float = Field(ge=-200, le=200)
    angular_velocity_x_dps: float = Field(ge=-2000, le=2000)
    angular_velocity_y_dps: float = Field(ge=-2000, le=2000)
    angular_velocity_z_dps: float = Field(ge=-2000, le=2000)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImuReading(ImuReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AmbientLightReadingCreate(BaseModel):
    illuminance_lux: float = Field(ge=0, le=150000)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AmbientLightReading(AmbientLightReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class WindReadingCreate(BaseModel):
    wind_speed_mps: float = Field(ge=0, le=100)
    wind_direction_degrees: float = Field(ge=0, lt=360)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WindReading(WindReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class MarineCurrentReadingCreate(BaseModel):
    current_speed_mps: float = Field(ge=0, le=20)
    current_direction_degrees: float = Field(ge=0, lt=360)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MarineCurrentReading(MarineCurrentReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class TurbidityReadingCreate(BaseModel):
    turbidity_ntu: float = Field(ge=TURBIDITY_MIN_NTU, le=TURBIDITY_MAX_NTU)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TurbidityReading(TurbidityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class DissolvedOxygenReadingCreate(BaseModel):
    dissolved_oxygen_mg_l: float = Field(
        ge=DISSOLVED_OXYGEN_MIN_MG_L,
        le=DISSOLVED_OXYGEN_MAX_MG_L,
    )
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DissolvedOxygenReading(DissolvedOxygenReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class PHReadingCreate(BaseModel):
    ph: float = Field(ge=PH_MIN, le=PH_MAX)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PHReading(PHReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class ConductivityReadingCreate(BaseModel):
    conductivity_us_cm: float = Field(ge=0, le=200000)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConductivityReading(ConductivityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class ChlorophyllAReadingCreate(BaseModel):
    chlorophyll_a_ug_l: float = Field(ge=0, le=1000)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChlorophyllAReading(ChlorophyllAReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class RainfallReadingCreate(BaseModel):
    rainfall_mm_h: float = Field(ge=0, le=500)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RainfallReading(RainfallReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class HumidityReadingCreate(BaseModel):
    humidity_percent: float = Field(
        ge=HUMIDITY_MIN_PERCENT,
        le=HUMIDITY_MAX_PERCENT,
    )
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumidityReading(HumidityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AirTemperatureReadingCreate(BaseModel):
    air_temperature_celsius: float = Field(
        ge=AIR_TEMPERATURE_MIN_CELSIUS,
        le=AIR_TEMPERATURE_MAX_CELSIUS,
    )
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AirTemperatureReading(AirTemperatureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AtmosphericPressureReadingCreate(BaseModel):
    atmospheric_pressure_kpa: float = Field(
        ge=ATMOSPHERIC_PRESSURE_MIN_KPA,
        le=ATMOSPHERIC_PRESSURE_MAX_KPA,
    )
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AtmosphericPressureReading(AtmosphericPressureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AcousticAltimeterReadingCreate(BaseModel):
    depth_meters: float = Field(ge=0, le=20000)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AcousticAltimeterReading(AcousticAltimeterReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class UnderwaterAcousticReadingCreate(BaseModel):
    echo_intensity_db: float = Field(ge=-200, le=100)
    sensor_channel: SensorChannel = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: ReadingQuality = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnderwaterAcousticReading(UnderwaterAcousticReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class TelemetryIngestResponse(BaseModel):
    buoy_id: str
    accepted_readings: int
    accepted_by_family: dict[str, int]
