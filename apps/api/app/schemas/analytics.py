"""HTTP contracts for telemetry analytics and temperature alerts."""

from datetime import datetime

from pydantic import BaseModel

from ..domain.analysis import AnalysisConfidence, SeaState
from ..domain.temperature import TemperatureTrend
from ..domain.temperature_alert import TemperatureAlertSeverity, TemperatureAlertStatus
from ..domain.wave import WaveConfidence


class PressureAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    latest_pressure_kpa: float | None = None
    average_pressure_kpa: float | None = None
    minimum_pressure_kpa: float | None = None
    maximum_pressure_kpa: float | None = None
    pressure_range_kpa: float | None = None
    estimated_wave_height_m: float | None = None
    confidence: AnalysisConfidence = "insufficient_data"
    sea_state: SeaState = "unknown"


class WaveAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    rejected_gnss_sample_count: int = 0
    gnss_vertical_range_m: float | None = None
    imu_vertical_acceleration_range_mps2: float | None = None
    estimated_wave_height_m: float | None = None
    estimated_period_seconds: float | None = None
    period_confidence: WaveConfidence = "insufficient_data"
    confidence: WaveConfidence = "insufficient_data"


class MovementAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    distance_travelled_m: float | None = None
    displacement_m: float | None = None
    average_speed_mps: float | None = None
    confidence: AnalysisConfidence = "insufficient_data"


class TemperatureAnalysis(BaseModel):
    buoy_id: str
    sample_count: int
    latest_temperature: float | None = None
    average_temperature: float | None = None
    minimum_temperature: float | None = None
    maximum_temperature: float | None = None
    change_celsius: float | None = None
    trend: TemperatureTrend = "insufficient_data"
    is_anomaly: bool = False
    anomaly_reason: str | None = None


class TemperatureAlert(BaseModel):
    buoy_id: str
    buoy_name: str
    severity: TemperatureAlertSeverity
    temperature_celsius: float
    average_temperature: float
    created_at: datetime
    message: str


class StoredTemperatureAlert(TemperatureAlert):
    id: int
    status: TemperatureAlertStatus
    resolved_at: datetime | None = None
