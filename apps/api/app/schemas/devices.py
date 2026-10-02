"""HTTP contracts for buoy device management."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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


class DeviceHealth(BaseModel):
    buoy_id: str
    device_id: str
    sensor_channel: Literal["A", "B"]
    status: Literal["active", "maintenance", "inactive"]
    last_seen_at: datetime | None = None
    age_seconds: float | None = None
    is_stale: bool
