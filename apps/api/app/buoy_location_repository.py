"""SQLAlchemy adapter for buoy location persistence and current coordinates."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .domain.buoy import BuoyLocationCommand, BuoySnapshot
from .domain.telemetry import LocationTelemetrySnapshot
from .entities import BuoyEntity, BuoyLocationReadingEntity
from .persistence_mappers import buoy_snapshot


class BuoyLocationRepository:
    """Persist location history and keep the buoy's current position in sync."""

    def __init__(self, db: Session) -> None:
        self.db = db

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
    ) -> BuoyLocationReadingEntity:
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
        return entity
