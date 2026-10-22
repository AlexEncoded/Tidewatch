"""SQLAlchemy adapter for physical-device registration and operations."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .domain.devices import (
    DeviceRegistrationCommand,
    DeviceRegistrationConflict,
    DeviceSnapshot,
    DeviceStatusCommand,
)
from .fleet_entities import BuoyEntity, DeviceEntity
from .persistence_mappers import device_snapshot
from .persistence_utils import is_newer_timestamp


class DeviceRepository:
    """Persistence adapter for physical buoy units, separate from telemetry storage."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.db.get(BuoyEntity, buoy_id) is not None

    def create_device(
        self, buoy_id: str, device: DeviceRegistrationCommand
    ) -> DeviceEntity:
        entity = DeviceEntity(
            device_id=device.device_id,
            buoy_id=buoy_id,
            sensor_channel=device.sensor_channel,
            firmware_version=device.firmware_version,
            registered_at=datetime.now(timezone.utc),
        )
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if self.get_device(device.device_id) is not None or any(
                existing.sensor_channel == device.sensor_channel
                for existing in self.list_devices(buoy_id)
            ):
                raise DeviceRegistrationConflict(
                    "Device or sensor channel already registered"
                ) from None
            raise
        self.db.refresh(entity)
        return entity

    def create_device_snapshot(
        self, buoy_id: str, device: DeviceRegistrationCommand
    ) -> DeviceSnapshot:
        return device_snapshot(self.create_device(buoy_id, device))

    def list_devices(self, buoy_id: str) -> list[DeviceEntity]:
        query = (
            select(DeviceEntity)
            .where(DeviceEntity.buoy_id == buoy_id)
            .order_by(DeviceEntity.sensor_channel)
        )
        return list(self.db.scalars(query).all())

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        return [device_snapshot(device) for device in self.list_devices(buoy_id)]

    def get_device(self, device_id: str) -> DeviceEntity | None:
        return self.db.get(DeviceEntity, device_id)

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        device = self.get_device(device_id)
        return device_snapshot(device) if device is not None else None

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        device = self.get_device(device_id)
        if device is None:
            return None
        self.mark_device_seen(device, seen_at)
        return self.get_device_snapshot(device_id)

    def mark_device_seen(self, device: DeviceEntity, seen_at: datetime) -> DeviceEntity:
        if is_newer_timestamp(seen_at, device.last_seen_at):
            device.last_seen_at = seen_at
            self.db.commit()
            self.db.refresh(device)
        return device

    def update_device_status(
        self, buoy_id: str, device_id: str, update: DeviceStatusCommand
    ) -> DeviceSnapshot | None:
        device = self.get_device(device_id)
        if device is None or device.buoy_id != buoy_id:
            return None
        device.status = update.status
        self.db.commit()
        self.db.refresh(device)
        return device_snapshot(device)
