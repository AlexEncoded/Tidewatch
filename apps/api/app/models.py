from datetime import datetime, timezone

from pydantic import BaseModel, Field


class BuoyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class Buoy(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TemperatureReadingCreate(BaseModel):
    temperature_celsius: float = Field(ge=-5, le=45)
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TemperatureReading(TemperatureReadingCreate):
    buoy_id: str

    model_config = {"from_attributes": True}


class BuoySummary(BaseModel):
    buoy: Buoy
    latest_temperature: TemperatureReading | None = None


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
