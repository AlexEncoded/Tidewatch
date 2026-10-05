"""HTTP contracts for buoy fleet operations."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from ..domain.buoy import (
    BUOY_NAME_MAX_LENGTH,
    BUOY_NAME_MIN_LENGTH,
    LATITUDE_MAX,
    LATITUDE_MIN,
    LONGITUDE_MAX,
    LONGITUDE_MIN,
    BuoyOperationalStatus,
)


class BuoyCreate(BaseModel):
    name: str = Field(min_length=BUOY_NAME_MIN_LENGTH, max_length=BUOY_NAME_MAX_LENGTH)
    latitude: float | None = Field(default=None, ge=LATITUDE_MIN, le=LATITUDE_MAX)
    longitude: float | None = Field(default=None, ge=LONGITUDE_MIN, le=LONGITUDE_MAX)


class BuoyStatusUpdate(BaseModel):
    status: BuoyOperationalStatus


class BuoyLocationUpdate(BaseModel):
    latitude: float = Field(ge=LATITUDE_MIN, le=LATITUDE_MAX)
    longitude: float = Field(ge=LONGITUDE_MIN, le=LONGITUDE_MAX)


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
