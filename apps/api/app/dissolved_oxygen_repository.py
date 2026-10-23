"""SQLAlchemy adapter for dissolved-oxygen persistence and history queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .buoy_registry_repository import BuoyRegistryRepository
from .domain.telemetry import DissolvedOxygenTelemetrySnapshot
from .sensor_entities import DissolvedOxygenReadingEntity


class DissolvedOxygenRepository:
    """Persist dissolved-oxygen samples and refresh buoy activity."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def add_dissolved_oxygen(
        self, reading: DissolvedOxygenTelemetrySnapshot
    ) -> DissolvedOxygenTelemetrySnapshot:
        entity = DissolvedOxygenReadingEntity(
            buoy_id=reading.buoy_id,
            dissolved_oxygen_mg_l=reading.dissolved_oxygen_mg_l,
            sensor_channel=reading.sensor_channel,
            device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
            quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        self.registry.mark_buoy_seen_by_id(reading.buoy_id, reading.measured_at)
        return DissolvedOxygenTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            dissolved_oxygen_mg_l=entity.dissolved_oxygen_mg_l,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        query = (
            select(DissolvedOxygenReadingEntity)
            .where(DissolvedOxygenReadingEntity.buoy_id == buoy_id)
            .order_by(DissolvedOxygenReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(DissolvedOxygenReadingEntity.sensor_channel == sensor_channel)
        return [
            DissolvedOxygenTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                dissolved_oxygen_mg_l=entity.dissolved_oxygen_mg_l,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_dissolved_oxygen(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> DissolvedOxygenTelemetrySnapshot | None:
        readings = self.list_dissolved_oxygen(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None
