"""HTTP contracts for core sensor telemetry and ingestion responses."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class TemperatureReadingCreate(BaseModel):
    temperature_celsius: float = Field(ge=-5, le=45)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemperatureReading(TemperatureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class PressureReadingCreate(BaseModel):
    pressure_kpa: float = Field(ge=80, le=130)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PressureReading(PressureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class SalinityReadingCreate(BaseModel):
    salinity_psu: float = Field(ge=0, le=45)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
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
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImuReading(ImuReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AmbientLightReadingCreate(BaseModel):
    illuminance_lux: float = Field(ge=0, le=150000)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AmbientLightReading(AmbientLightReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class WindReadingCreate(BaseModel):
    wind_speed_mps: float = Field(ge=0, le=100)
    wind_direction_degrees: float = Field(ge=0, lt=360)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WindReading(WindReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class MarineCurrentReadingCreate(BaseModel):
    current_speed_mps: float = Field(ge=0, le=20)
    current_direction_degrees: float = Field(ge=0, lt=360)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MarineCurrentReading(MarineCurrentReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class TurbidityReadingCreate(BaseModel):
    turbidity_ntu: float = Field(ge=0, le=5000)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TurbidityReading(TurbidityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class DissolvedOxygenReadingCreate(BaseModel):
    dissolved_oxygen_mg_l: float = Field(ge=0, le=20)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DissolvedOxygenReading(DissolvedOxygenReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class PHReadingCreate(BaseModel):
    ph: float = Field(ge=0, le=14)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PHReading(PHReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class ConductivityReadingCreate(BaseModel):
    conductivity_us_cm: float = Field(ge=0, le=200000)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConductivityReading(ConductivityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class TelemetryIngestResponse(BaseModel):
    buoy_id: str
    accepted_readings: int
    accepted_by_family: dict[str, int]
