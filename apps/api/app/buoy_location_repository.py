"""SQLAlchemy adapter for buoy location persistence and current coordinates."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain.buoy import BuoyLocationCommand, BuoySnapshot
from .domain.telemetry import LocationTelemetrySnapshot
from .fleet_entities import BuoyEntity, BuoyLocationReadingEntity
from .persistence_mappers import buoy_snapshot


class BuoyLocationRepository:
    """Persist location history and keep the buoy's current position in sync."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.db.get(BuoyEntity, buoy_id) is not None

    @staticmethod
    def _location_snapshot(entity: BuoyLocationReadingEntity) -> LocationTelemetrySnapshot:
        return LocationTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            latitude=entity.latitude,
            longitude=entity.longitude,
            measured_at=entity.measured_at,
            altitude_meters=entity.altitude_meters,
            speed_mps=entity.speed_mps,
            hdop=entity.hdop,
            satellites=entity.satellites,
            device_id=entity.device_id,
        )

    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        query = (
            select(BuoyLocationReadingEntity)
            .where(BuoyLocationReadingEntity.buoy_id == buoy_id)
            .order_by(BuoyLocationReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if since is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at >= since)
        if until is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at <= until)
        return [
            self._location_snapshot(entity)
            for entity in self.db.scalars(query).all()
        ]

    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        query = select(BuoyLocationReadingEntity).order_by(
            BuoyLocationReadingEntity.measured_at.desc()
        ).limit(limit)
        if since is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at >= since)
        if until is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at <= until)
        return [
            self._location_snapshot(entity)
            for entity in self.db.scalars(query).all()
        ]

    def update_buoy_location(
        self, buoy_id: str, command: BuoyLocationCommand
    ) -> BuoySnapshot | None:
        buoy = self.db.get(BuoyEntity, buoy_id)
        if buoy is None:
            return None
        self.add_location(
            LocationTelemetrySnapshot(
                buoy_id=buoy_id,
                latitude=command.latitude,
                longitude=command.longitude,
                measured_at=datetime.now(timezone.utc),
            )
        )
        buoy = self.db.get(BuoyEntity, buoy_id)
        return buoy_snapshot(buoy) if buoy is not None else None

    def add_location(
        self, reading: LocationTelemetrySnapshot
    ) -> LocationTelemetrySnapshot:
        entity = BuoyLocationReadingEntity(
            buoy_id=reading.buoy_id,
            latitude=reading.latitude,
            longitude=reading.longitude,
            altitude_meters=reading.altitude_meters,
            speed_mps=reading.speed_mps,
            hdop=reading.hdop,
            satellites=reading.satellites,
            device_id=reading.device_id,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        buoy = self.db.get(BuoyEntity, reading.buoy_id)
        if buoy is not None:
            buoy.latitude = reading.latitude
            buoy.longitude = reading.longitude
            self.db.commit()
            self.db.refresh(buoy)
        return self._location_snapshot(entity)
