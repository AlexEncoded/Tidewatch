"""HTTP contracts for buoy battery telemetry and health."""

from datetime import datetime, timezone
from ..domain.telemetry_types import (
    BATTERY_MAX_PERCENT,
    BATTERY_MIN_PERCENT,
    SensorChannel,
)

from pydantic import BaseModel, Field


class BatteryReadingCreate(BaseModel):
    battery_percent: float = Field(
        ge=BATTERY_MIN_PERCENT,
        le=BATTERY_MAX_PERCENT,
    )
    device_id: SensorChannel = "A"
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
