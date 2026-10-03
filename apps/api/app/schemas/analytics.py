"""HTTP contracts for telemetry analytics and temperature alerts."""

from datetime import datetime

from pydantic import BaseModel


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
