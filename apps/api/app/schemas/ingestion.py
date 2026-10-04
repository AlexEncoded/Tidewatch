"""HTTP request contracts for ingesting batches of buoy telemetry."""

from pydantic import BaseModel, Field, field_validator, model_validator

from .battery import BatteryReadingCreate
from .fleet import BuoyLocationReadingCreate
from .telemetry import (
    AcousticAltimeterReadingCreate,
    AirTemperatureReadingCreate,
    AmbientLightReadingCreate,
    AtmosphericPressureReadingCreate,
    ChlorophyllAReadingCreate,
    ConductivityReadingCreate,
    DissolvedOxygenReadingCreate,
    HumidityReadingCreate,
    ImuReadingCreate,
    MarineCurrentReadingCreate,
    PHReadingCreate,
    PressureReadingCreate,
    RainfallReadingCreate,
    SalinityReadingCreate,
    TemperatureReadingCreate,
    TurbidityReadingCreate,
    UnderwaterAcousticReadingCreate,
    WindReadingCreate,
)


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
