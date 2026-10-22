"""SQLAlchemy adapter for turbidity telemetry persistence and queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .buoy_registry_repository import BuoyRegistryRepository
from .domain.telemetry import TurbidityTelemetrySnapshot
from .persistence_utils import is_newer_timestamp
from .sensor_entities import TurbidityReadingEntity


class TurbidityRepository:
    """Persist turbidity samples and refresh their buoy heartbeat."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def add_turbidity(
        self, reading: TurbidityTelemetrySnapshot
    ) -> TurbidityTelemetrySnapshot:
        entity = TurbidityReadingEntity(
            buoy_id=reading.buoy_id,
            turbidity_ntu=reading.turbidity_ntu,
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
        return TurbidityTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            turbidity_ntu=entity.turbidity_ntu,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        query = (
            select(TurbidityReadingEntity)
            .where(TurbidityReadingEntity.buoy_id == buoy_id)
            .order_by(TurbidityReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(TurbidityReadingEntity.sensor_channel == sensor_channel)
        return [
            TurbidityTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                turbidity_ntu=entity.turbidity_ntu,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_turbidity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TurbidityTelemetrySnapshot | None:
        readings = self.list_turbidity(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None
