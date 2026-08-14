from sqlalchemy import select
from sqlalchemy.orm import Session

from .entities import BuoyEntity, TemperatureReadingEntity
from .models import Buoy, TemperatureReading


class BuoyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_buoy(self, buoy: Buoy) -> BuoyEntity:
        entity = BuoyEntity(id=buoy.id, name=buoy.name, created_at=buoy.created_at)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_buoy(self, buoy_id: str) -> BuoyEntity | None:
        return self.db.get(BuoyEntity, buoy_id)

    def list_buoys(self) -> list[BuoyEntity]:
        return list(self.db.scalars(select(BuoyEntity).order_by(BuoyEntity.created_at)).all())

    def add_temperature(self, reading: TemperatureReading) -> TemperatureReadingEntity:
        entity = TemperatureReadingEntity(
            buoy_id=reading.buoy_id,
            temperature_celsius=reading.temperature_celsius,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def list_temperatures(self, buoy_id: str, limit: int) -> list[TemperatureReadingEntity]:
        query = (
            select(TemperatureReadingEntity)
            .where(TemperatureReadingEntity.buoy_id == buoy_id)
            .order_by(TemperatureReadingEntity.measured_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())

    def latest_temperature(self, buoy_id: str) -> TemperatureReadingEntity | None:
        readings = self.list_temperatures(buoy_id, limit=1)
        return readings[0] if readings else None
