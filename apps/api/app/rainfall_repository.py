"""SQLAlchemy adapter for rainfall telemetry persistence and queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .buoy_registry_repository import BuoyRegistryRepository
from .domain.telemetry import RainfallTelemetrySnapshot
from .entities import RainfallReadingEntity
from .persistence_utils import is_newer_timestamp


class RainfallRepository:
    """Persist rainfall readings and refresh buoy activity."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def add_rainfall(
        self, reading: RainfallTelemetrySnapshot
    ) -> RainfallTelemetrySnapshot:
        entity = RainfallReadingEntity(
            buoy_id=reading.buoy_id,
            rainfall_mm_h=reading.rainfall_mm_h,
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
        buoy = self.registry.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(
            reading.measured_at, buoy.last_seen_at
        ):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return RainfallTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            rainfall_mm_h=entity.rainfall_mm_h,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        query = (
            select(RainfallReadingEntity)
            .where(RainfallReadingEntity.buoy_id == buoy_id)
            .order_by(RainfallReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(
                RainfallReadingEntity.sensor_channel == sensor_channel
            )
        return [
            RainfallTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                rainfall_mm_h=entity.rainfall_mm_h,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_rainfall(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> RainfallTelemetrySnapshot | None:
        readings = self.list_rainfall(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None
