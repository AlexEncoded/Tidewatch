from datetime import datetime, timezone

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class BuoyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class BuoyStatusUpdate(BaseModel):
    status: Literal["active", "maintenance", "inactive"]


class BuoyLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class BuoyLocationReadingCreate(BuoyLocationUpdate):
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BuoyLocationReading(BuoyLocationReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class Buoy(BaseModel):
    id: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    status: str = "active"
    last_seen_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BuoyHealth(BaseModel):
    buoy_id: str
    buoy_name: str
    status: str
    last_seen_at: datetime | None = None
    age_seconds: float | None = None
    is_stale: bool


class TemperatureReadingCreate(BaseModel):
    temperature_celsius: float = Field(ge=-5, le=45)
    sensor_channel: Literal["A", "B"] = "A"
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
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AmbientLightReading(AmbientLightReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class BatteryReadingCreate(BaseModel):
    battery_percent: float = Field(ge=0, le=100)
    device_id: Literal["A", "B"] = "A"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatteryReading(BatteryReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class BatteryHealth(BaseModel):
    buoy_id: str
    status: str
    device_a_percent: float | None = None
    device_b_percent: float | None = None
    delta_percent: float | None = None
    degraded_devices: list[str] = []
    checked_at: datetime


class BatteryAnalysis(BaseModel):
    buoy_id: str
    device_id: str
    sample_count: int
    latest_percent: float | None = None
    oldest_percent: float | None = None
    change_percent: float | None = None
    discharge_rate_percent_per_hour: float | None = None
    estimated_hours_remaining: float | None = None
    confidence: str = "insufficient_data"


class TelemetryBatchCreate(BaseModel):
    temperatures: list[TemperatureReadingCreate] = Field(default_factory=list, max_length=100)
    pressures: list[PressureReadingCreate] = Field(default_factory=list, max_length=100)
    salinity: list[SalinityReadingCreate] = Field(default_factory=list, max_length=100)
    imu: list[ImuReadingCreate] = Field(default_factory=list, max_length=100)
    ambient_light: list[AmbientLightReadingCreate] = Field(default_factory=list, max_length=100)
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
            or self.battery
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
        ):
            channels = [reading.sensor_channel for reading in readings]
            if len(channels) != len(set(channels)):
                raise ValueError(f"Telemetry batch cannot contain duplicate {family} channels")
        return self


class TelemetryIngestResponse(BaseModel):
    buoy_id: str
    accepted_readings: int
    accepted_by_family: dict[str, int]


class PressureAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    latest_pressure_kpa: float | None = None
    average_pressure_kpa: float | None = None
    minimum_pressure_kpa: float | None = None
    maximum_pressure_kpa: float | None = None
    pressure_range_kpa: float | None = None
    estimated_wave_height_m: float | None = None
    confidence: str = "insufficient_data"
    sea_state: str = "unknown"


class MovementAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    distance_travelled_m: float | None = None
    displacement_m: float | None = None
    average_speed_mps: float | None = None
    confidence: str = "insufficient_data"


class SensorHealth(BaseModel):
    buoy_id: str
    status: str
    temperature_delta_celsius: float | None = None
    pressure_delta_kpa: float | None = None
    salinity_delta_psu: float | None = None
    imu_acceleration_delta_mps2: float | None = None
    ambient_light_delta_lux: float | None = None
    degraded_sensors: list[str] = []
    missing_sensors: list[str] = []
    decisions: dict[str, str] = Field(default_factory=dict)
    checked_at: datetime


class SensorHealthCheck(SensorHealth):
    id: int

    model_config = {"from_attributes": True}


class MaintenanceIssue(BaseModel):
    buoy_id: str
    buoy_name: str
    issue_type: str
    severity: str
    message: str


class MaintenanceNotificationResult(BaseModel):
    status: str
    issue_count: int


class QualitySummary(BaseModel):
    buoy_id: str
    total_readings: int
    good_readings: int
    suspect_readings: int
    invalid_readings: int


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
    latest_battery: BatteryReading | None = None
    latest_battery_a: BatteryReading | None = None
    latest_battery_b: BatteryReading | None = None


class TemperatureAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    latest_temperature: float | None = None
    average_temperature: float | None = None
    minimum_temperature: float | None = None
    maximum_temperature: float | None = None
    change_celsius: float | None = None
    trend: str = "insufficient_data"
    is_anomaly: bool = False
    anomaly_reason: str | None = None


class TemperatureAlert(BaseModel):
    buoy_id: str
    buoy_name: str
    severity: str
    temperature_celsius: float
    average_temperature: float
    created_at: datetime
    message: str


class StoredTemperatureAlert(TemperatureAlert):
    id: int
    status: str
    resolved_at: datetime | None = None
