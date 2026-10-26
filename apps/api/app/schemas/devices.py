"""HTTP contracts for buoy device management."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

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


class DeviceRuntimeTelemetry(BaseModel):
    cpu_usage_percent: float = Field(ge=0, le=100)
    memory_usage_percent: float = Field(ge=0, le=100)
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceCommunicationTelemetry(BaseModel):
    packet_loss_percent: float | None = Field(default=None, ge=0, le=100)
    round_trip_latency_ms: float | None = Field(default=None, ge=0, le=600_000)
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def require_a_communication_measurement(self) -> "DeviceCommunicationTelemetry":
        if self.packet_loss_percent is None and self.round_trip_latency_ms is None:
            raise ValueError("At least one communication measurement is required")
        return self


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
