"""SQLAlchemy adapter for buoy registration and operational status."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain.buoy import BuoySnapshot, BuoyStatusCommand
from .entities import BuoyEntity
from .persistence_mappers import buoy_snapshot
from .persistence_utils import is_newer_timestamp


class BuoyRegistryRepository:
    """Persist fleet identity and status independently from telemetry."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_buoy(self, buoy_id: str) -> BuoyEntity | None:
        return self.db.get(BuoyEntity, buoy_id)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.get_buoy(buoy_id) is not None

    def mark_buoy_seen_by_id(
        self, buoy_id: str, seen_at: datetime
    ) -> BuoySnapshot | None:
        buoy = self.get_buoy(buoy_id)
        if buoy is None:
            return None
        if is_newer_timestamp(seen_at, buoy.last_seen_at):
            buoy.last_seen_at = seen_at
            self.db.commit()
            self.db.refresh(buoy)
        return buoy_snapshot(buoy)

    def list_buoys(self) -> list[BuoyEntity]:
        return list(
            self.db.scalars(
                select(BuoyEntity).order_by(BuoyEntity.created_at)
            ).all()
        )

    def list_buoy_snapshots(self) -> list[BuoySnapshot]:
        return [buoy_snapshot(buoy) for buoy in self.list_buoys()]

    def register_buoy(self, buoy: BuoySnapshot) -> BuoySnapshot:
        entity = BuoyEntity(
            id=buoy.buoy_id,
            name=buoy.name,
            latitude=buoy.latitude,
            longitude=buoy.longitude,
            status=buoy.status,
            last_seen_at=buoy.last_seen_at,
            created_at=buoy.created_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return buoy_snapshot(entity)

    def update_buoy_status(
        self, buoy_id: str, command: BuoyStatusCommand
    ) -> BuoySnapshot | None:
        buoy = self.db.get(BuoyEntity, buoy_id)
        if buoy is None:
            return None
        buoy.status = command.status
        self.db.commit()
        self.db.refresh(buoy)
        return buoy_snapshot(buoy)
