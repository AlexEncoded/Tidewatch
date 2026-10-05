"""HTTP contracts for buoy device management."""

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.devices import (
    DEVICE_FIRMWARE_MAX_LENGTH,
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    DeviceOperationalStatus,
    DeviceSensorChannel,
)


class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=DEVICE_ID_MIN_LENGTH, max_length=DEVICE_ID_MAX_LENGTH)
    sensor_channel: DeviceSensorChannel
    firmware_version: str | None = Field(default=None, max_length=DEVICE_FIRMWARE_MAX_LENGTH)


class DeviceStatusUpdate(BaseModel):
    status: DeviceOperationalStatus


class Device(BaseModel):
    buoy_id: str
    device_id: str
    sensor_channel: DeviceSensorChannel
    firmware_version: str | None = None
    status: DeviceOperationalStatus = "active"
    registered_at: datetime
    last_seen_at: datetime | None = None

    model_config = {"from_attributes": True}


class DeviceHealth(BaseModel):
    buoy_id: str
    device_id: str
    sensor_channel: DeviceSensorChannel
    status: DeviceOperationalStatus
    last_seen_at: datetime | None = None
    age_seconds: float | None = None
    is_stale: bool
