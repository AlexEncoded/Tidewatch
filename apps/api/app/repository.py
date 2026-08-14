from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .entities import (
    BuoyEntity,
    PressureReadingEntity,
    TemperatureAlertEntity,
    TemperatureReadingEntity,
)
from .models import (
    Buoy,
    BuoyStatusUpdate,
    PressureReading,
    TemperatureAlert,
    TemperatureReading,
)


class BuoyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_buoy(self, buoy: Buoy) -> BuoyEntity:
        entity = BuoyEntity(
            id=buoy.id,
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
        return entity

    def update_status(self, buoy_id: str, update: BuoyStatusUpdate) -> BuoyEntity | None:
        buoy = self.get_buoy(buoy_id)
        if buoy is None:
            return None
        buoy.status = update.status
        self.db.commit()
        self.db.refresh(buoy)
        return buoy

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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and (
            buoy.last_seen_at is None or reading.measured_at > buoy.last_seen_at
        ):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
            self.db.refresh(buoy)
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

    def add_pressure(self, reading: PressureReading) -> PressureReadingEntity:
        entity = PressureReadingEntity(
            buoy_id=reading.buoy_id,
            pressure_kpa=reading.pressure_kpa,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and (
            buoy.last_seen_at is None or reading.measured_at > buoy.last_seen_at
        ):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return entity

    def list_pressures(self, buoy_id: str, limit: int) -> list[PressureReadingEntity]:
        query = (
            select(PressureReadingEntity)
            .where(PressureReadingEntity.buoy_id == buoy_id)
            .order_by(PressureReadingEntity.measured_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())

    def latest_pressure(self, buoy_id: str) -> PressureReadingEntity | None:
        readings = self.list_pressures(buoy_id, limit=1)
        return readings[0] if readings else None

    def find_alert(self, buoy_id: str, measured_at: datetime) -> TemperatureAlertEntity | None:
        query = select(TemperatureAlertEntity).where(
            TemperatureAlertEntity.buoy_id == buoy_id,
            TemperatureAlertEntity.reading_measured_at == measured_at,
        )
        return self.db.scalars(query).first()

    def create_alert(self, alert: TemperatureAlert, measured_at: datetime) -> TemperatureAlertEntity:
        entity = TemperatureAlertEntity(
            buoy_id=alert.buoy_id,
            reading_measured_at=measured_at,
            severity=alert.severity,
            temperature_celsius=alert.temperature_celsius,
            average_temperature=alert.average_temperature,
            message=alert.message,
            status="open",
            created_at=alert.created_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def list_alerts(self, status: str = "open") -> list[TemperatureAlertEntity]:
        query = select(TemperatureAlertEntity).where(
            TemperatureAlertEntity.status == status
        ).order_by(TemperatureAlertEntity.created_at.desc())
        return list(self.db.scalars(query).all())

    def resolve_alert(self, alert_id: int) -> TemperatureAlertEntity | None:
        alert = self.db.get(TemperatureAlertEntity, alert_id)
        if alert is None:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.now(alert.created_at.tzinfo)
        self.db.commit()
        self.db.refresh(alert)
        return alert
