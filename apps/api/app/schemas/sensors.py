"""HTTP contracts for sensor health and history."""

from datetime import datetime

from pydantic import BaseModel, Field


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
