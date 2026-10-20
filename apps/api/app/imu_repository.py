"""SQLAlchemy adapter for IMU telemetry persistence and queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .buoy_registry_repository import BuoyRegistryRepository
from .domain.telemetry import ImuTelemetrySnapshot
from .persistence_utils import is_newer_timestamp
from .sensor_entities import ImuReadingEntity


class ImuRepository:
    """Persist inertial samples and refresh their buoy heartbeat."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def add_imu(self, reading: ImuTelemetrySnapshot) -> ImuTelemetrySnapshot:
        entity = ImuReadingEntity(
            buoy_id=reading.buoy_id,
            acceleration_x_mps2=reading.acceleration_x_mps2,
            acceleration_y_mps2=reading.acceleration_y_mps2,
            acceleration_z_mps2=reading.acceleration_z_mps2,
            angular_velocity_x_dps=reading.angular_velocity_x_dps,
            angular_velocity_y_dps=reading.angular_velocity_y_dps,
            angular_velocity_z_dps=reading.angular_velocity_z_dps,
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
        return ImuTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            acceleration_x_mps2=entity.acceleration_x_mps2,
            acceleration_y_mps2=entity.acceleration_y_mps2,
            acceleration_z_mps2=entity.acceleration_z_mps2,
            angular_velocity_x_dps=entity.angular_velocity_x_dps,
            angular_velocity_y_dps=entity.angular_velocity_y_dps,
            angular_velocity_z_dps=entity.angular_velocity_z_dps,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        query = (
            select(ImuReadingEntity)
            .where(ImuReadingEntity.buoy_id == buoy_id)
            .order_by(ImuReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(ImuReadingEntity.sensor_channel == sensor_channel)
        return [
            ImuTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                acceleration_x_mps2=entity.acceleration_x_mps2,
                acceleration_y_mps2=entity.acceleration_y_mps2,
                acceleration_z_mps2=entity.acceleration_z_mps2,
                angular_velocity_x_dps=entity.angular_velocity_x_dps,
                angular_velocity_y_dps=entity.angular_velocity_y_dps,
                angular_velocity_z_dps=entity.angular_velocity_z_dps,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_imu(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ImuTelemetrySnapshot | None:
        readings = self.list_imu(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None
