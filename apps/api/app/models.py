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
