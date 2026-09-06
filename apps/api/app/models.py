from datetime import datetime, timezone

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class BuoyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class BuoyStatusUpdate(BaseModel):
    status: Literal["active", "maintenance", "inactive"]


class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    sensor_channel: Literal["A", "B"]
    firmware_version: str | None = Field(default=None, max_length=50)


class DeviceStatusUpdate(BaseModel):
    status: Literal["active", "maintenance", "inactive"]


class Device(BaseModel):
    buoy_id: str
    device_id: str
    sensor_channel: Literal["A", "B"]
    firmware_version: str | None = None
    status: Literal["active", "maintenance", "inactive"] = "active"
    registered_at: datetime
    last_seen_at: datetime | None = None

    model_config = {"from_attributes": True}


class BuoyLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class BuoyLocationReadingCreate(BuoyLocationUpdate):
    altitude_meters: float | None = Field(default=None, ge=-1000, le=20000)
    speed_mps: float | None = Field(default=None, ge=0, le=100)
    hdop: float | None = Field(default=None, gt=0, le=100)
    satellites: int | None = Field(default=None, ge=0, le=100)
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
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


class ChlorophyllAReadingCreate(BaseModel):
    chlorophyll_a_ug_l: float = Field(ge=0, le=1000)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChlorophyllAReading(ChlorophyllAReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class RainfallReadingCreate(BaseModel):
    rainfall_mm_h: float = Field(ge=0, le=500)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RainfallReading(RainfallReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class HumidityReadingCreate(BaseModel):
    humidity_percent: float = Field(ge=0, le=100)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumidityReading(HumidityReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AirTemperatureReadingCreate(BaseModel):
    air_temperature_celsius: float = Field(ge=-60, le=60)
    sensor_channel: Literal["A", "B"] = "A"
    device_id: str | None = Field(default=None, min_length=1, max_length=100)
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AirTemperatureReading(AirTemperatureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AtmosphericPressureReadingCreate(BaseModel):
    atmospheric_pressure_kpa: float = Field(ge=80, le=120)
    sensor_channel: Literal["A", "B"] = "A"
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AtmosphericPressureReading(AtmosphericPressureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class AcousticAltimeterReadingCreate(BaseModel):
    depth_meters: float = Field(ge=0, le=20000)
    sensor_channel: Literal["A", "B"] = "A"
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
    sensor_id: str | None = Field(default=None, max_length=100)
    firmware_version: str | None = Field(default=None, max_length=50)
    quality: Literal["good", "suspect", "invalid"] = "good"
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnderwaterAcousticReading(UnderwaterAcousticReadingCreate):
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


class WaveAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    gnss_vertical_range_m: float | None = None
    imu_vertical_acceleration_range_mps2: float | None = None
    estimated_wave_height_m: float | None = None
    estimated_period_seconds: float | None = None
    confidence: str = "insufficient_data"


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
    wind_speed_delta_mps: float | None = None
    wind_direction_delta_degrees: float | None = None
    marine_current_speed_delta_mps: float | None = None
    marine_current_direction_delta_degrees: float | None = None
    turbidity_delta_ntu: float | None = None
    dissolved_oxygen_delta_mg_l: float | None = None
    ph_delta: float | None = None
    conductivity_delta_us_cm: float | None = None
    chlorophyll_a_delta_ug_l: float | None = None
    rainfall_delta_mm_h: float | None = None
    humidity_delta_percent: float | None = None
    air_temperature_delta_celsius: float | None = None
    atmospheric_pressure_delta_kpa: float | None = None
    acoustic_altimeter_delta_meters: float | None = None
    underwater_acoustic_delta_db: float | None = None
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
