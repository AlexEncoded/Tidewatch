"""SQLAlchemy adapter for battery telemetry and device ownership queries."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .buoy_registry_repository import BuoyRegistryRepository
from .device_repository import DeviceRepository
from .domain.devices import DeviceSnapshot
from .domain.telemetry import BatteryTelemetrySnapshot
from .entities import DeviceEntity
from .sensor_entities import BatteryReadingEntity
from .persistence_utils import is_newer_timestamp


class BatteryRepository:
    """Persist battery readings while delegating device operations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.devices = DeviceRepository(db)
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.devices.buoy_exists(buoy_id)

    def get_device(self, device_id: str) -> DeviceEntity | None:
        return self.devices.get_device(device_id)

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        return self.devices.get_device_snapshot(device_id)

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        return self.devices.mark_device_seen_by_id(device_id, seen_at)

    def add_battery(
        self, reading: BatteryTelemetrySnapshot
    ) -> BatteryTelemetrySnapshot:
        entity = BatteryReadingEntity(
            buoy_id=reading.buoy_id,
            device_id=reading.device_id,
            physical_device_id=reading.physical_device_id,
            battery_percent=reading.battery_percent,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        buoy = self.registry.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(
            reading.measured_at, buoy.last_seen_at
        ):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return BatteryTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            battery_percent=entity.battery_percent,
            device_id=entity.device_id,
            measured_at=entity.measured_at,
            physical_device_id=entity.physical_device_id,
        )

    def latest_battery(
        self,
        buoy_id: str,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> BatteryTelemetrySnapshot | None:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(1)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        if physical_device_id is not None:
            query = query.where(
                BatteryReadingEntity.physical_device_id == physical_device_id
            )
        entity = self.db.scalars(query).first()
        if entity is None:
            return None
        return BatteryTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            battery_percent=entity.battery_percent,
            device_id=entity.device_id,
            measured_at=entity.measured_at,
            physical_device_id=entity.physical_device_id,
        )

    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> list[BatteryTelemetrySnapshot]:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        if physical_device_id is not None:
            query = query.where(
                BatteryReadingEntity.physical_device_id == physical_device_id
            )
        return [
            BatteryTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                battery_percent=entity.battery_percent,
                device_id=entity.device_id,
                measured_at=entity.measured_at,
                physical_device_id=entity.physical_device_id,
            )
            for entity in self.db.scalars(query).all()
        ]
