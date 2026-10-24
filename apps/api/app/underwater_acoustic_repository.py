"""SQLAlchemy adapter for underwater-acoustic telemetry persistence and queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .buoy_registry_repository import BuoyRegistryRepository
from .domain.telemetry import UnderwaterAcousticTelemetrySnapshot
from .sensor_entities import UnderwaterAcousticReadingEntity


class UnderwaterAcousticRepository:
    """Persist underwater-acoustic readings and refresh buoy activity."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def add_underwater_acoustic(
        self, reading: UnderwaterAcousticTelemetrySnapshot
    ) -> UnderwaterAcousticTelemetrySnapshot:
        entity = UnderwaterAcousticReadingEntity(
            buoy_id=reading.buoy_id,
            echo_intensity_db=reading.echo_intensity_db,
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
        return UnderwaterAcousticTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            echo_intensity_db=entity.echo_intensity_db,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_underwater_acoustic(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[UnderwaterAcousticTelemetrySnapshot]:
        query = (
            select(UnderwaterAcousticReadingEntity)
            .where(UnderwaterAcousticReadingEntity.buoy_id == buoy_id)
            .order_by(UnderwaterAcousticReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(
                UnderwaterAcousticReadingEntity.sensor_channel == sensor_channel
            )
        return [
            UnderwaterAcousticTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                echo_intensity_db=entity.echo_intensity_db,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_underwater_acoustic(
        self, buoy_id: str, sensor_channel: str | None = "A"
    ) -> UnderwaterAcousticTelemetrySnapshot | None:
        readings = self.list_underwater_acoustic(buoy_id, 1, sensor_channel)
        return readings[0] if readings else None
