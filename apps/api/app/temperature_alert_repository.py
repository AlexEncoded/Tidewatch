"""SQLAlchemy adapter composing temperature reads and alert persistence."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain.buoy import BuoyIdentitySnapshot
from .domain.temperature import TemperatureTelemetrySnapshot
from .domain.temperature_alert import (
    TemperatureAlertSnapshot,
    TemperatureAnomalySnapshot,
)
from .entities import BuoyEntity, TemperatureAlertEntity
from .repository import BuoyRepository


class TemperatureAlertRepository:
    """Provide temperature-alert ports while composing the telemetry reader."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.telemetry = BuoyRepository(db)

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        return self.telemetry.list_temperatures(buoy_id, limit, sensor_channel)

    def list_buoy_identities(self) -> list[BuoyIdentitySnapshot]:
        buoys = self.db.scalars(
            select(BuoyEntity).order_by(BuoyEntity.created_at)
        ).all()
        return [
            BuoyIdentitySnapshot(buoy_id=buoy.id, name=buoy.name)
            for buoy in buoys
        ]

    def _snapshot(self, entity: TemperatureAlertEntity) -> TemperatureAlertSnapshot:
        return TemperatureAlertSnapshot(
            id=entity.id,
            buoy_id=entity.buoy_id,
            buoy_name=entity.buoy.name,
            severity=entity.severity,
            temperature_celsius=entity.temperature_celsius,
            average_temperature=entity.average_temperature,
            created_at=entity.created_at,
            message=entity.message,
            status=entity.status,
            resolved_at=entity.resolved_at,
        )

    def find_alert(
        self, buoy_id: str, measured_at: datetime
    ) -> TemperatureAlertSnapshot | None:
        query = select(TemperatureAlertEntity).where(
            TemperatureAlertEntity.buoy_id == buoy_id,
            TemperatureAlertEntity.reading_measured_at == measured_at,
        )
        entity = self.db.scalars(query).first()
        return self._snapshot(entity) if entity is not None else None

    def create_alert(
        self,
        alert: TemperatureAnomalySnapshot,
        measured_at: datetime,
    ) -> TemperatureAlertSnapshot:
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
        return self._snapshot(entity)

    def list_alerts(self, status: str = "open") -> list[TemperatureAlertSnapshot]:
        query = (
            select(TemperatureAlertEntity)
            .where(TemperatureAlertEntity.status == status)
            .order_by(TemperatureAlertEntity.created_at.desc())
        )
        return [self._snapshot(entity) for entity in self.db.scalars(query).all()]

    def resolve_alert(self, alert_id: int) -> TemperatureAlertSnapshot | None:
        alert = self.db.get(TemperatureAlertEntity, alert_id)
        if alert is None:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.now(alert.created_at.tzinfo)
        self.db.commit()
        self.db.refresh(alert)
        return self._snapshot(alert)
