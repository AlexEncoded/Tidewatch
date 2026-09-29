from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .entities import (
    BuoyEntity,
    DeviceEntity,
    SensorHealthCheckEntity,
    BuoyLocationReadingEntity,
    BatteryReadingEntity,
    ImuReadingEntity,
    AmbientLightReadingEntity,
    WindReadingEntity,
    MarineCurrentReadingEntity,
    TurbidityReadingEntity,
    DissolvedOxygenReadingEntity,
    PHReadingEntity,
    ConductivityReadingEntity,
    ChlorophyllAReadingEntity,
    RainfallReadingEntity,
    HumidityReadingEntity,
    AirTemperatureReadingEntity,
    AtmosphericPressureReadingEntity,
    AcousticAltimeterReadingEntity,
    UnderwaterAcousticReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    TemperatureAlertEntity,
    TemperatureReadingEntity,
)
from .domain.devices import (
    DeviceRegistrationCommand,
    DeviceRegistrationConflict,
    DeviceStatusCommand,
)
from .domain.buoy import (
    BuoyActivitySnapshot,
    BuoyIdentitySnapshot,
    BuoySnapshot,
    BuoyStatusCommand,
    BuoyLocationCommand,
)
from .domain.temperature_alert import TemperatureAlertSnapshot, TemperatureAnomalySnapshot
from .domain.pressure import PressureTelemetrySnapshot
from .domain.telemetry import (
    AmbientLightTelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    RainfallTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    AirTemperatureTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    AcousticAltimeterTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
    BatteryTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    ImuTelemetrySnapshot,
    LocationTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    WindTelemetrySnapshot,
)
from .domain.temperature import TemperatureTelemetrySnapshot
from .models import (
    SensorHealth,
)


def _is_newer(candidate: datetime, previous: datetime | None) -> bool:
    """Compare timestamps consistently across PostgreSQL and SQLite."""
    if previous is None:
        return True
    candidate_utc = candidate.astimezone(timezone.utc) if candidate.tzinfo else candidate.replace(tzinfo=timezone.utc)
    previous_utc = previous.astimezone(timezone.utc) if previous.tzinfo else previous.replace(tzinfo=timezone.utc)
    return candidate_utc > previous_utc


class BuoyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

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
        return BuoySnapshot(
            buoy_id=entity.id,
            name=entity.name,
            latitude=entity.latitude,
            longitude=entity.longitude,
            status=entity.status,
            last_seen_at=entity.last_seen_at,
            created_at=entity.created_at,
        )

    def update_buoy_status(
        self, buoy_id: str, command: BuoyStatusCommand
    ) -> BuoySnapshot | None:
        buoy = self.get_buoy(buoy_id)
        if buoy is None:
            return None
        buoy.status = command.status
        self.db.commit()
        self.db.refresh(buoy)
        return BuoySnapshot(
            buoy_id=buoy.id,
            name=buoy.name,
            latitude=buoy.latitude,
            longitude=buoy.longitude,
            status=buoy.status,
            last_seen_at=buoy.last_seen_at,
            created_at=buoy.created_at,
        )

    def update_buoy_location(
        self, buoy_id: str, command: BuoyLocationCommand
    ) -> BuoySnapshot | None:
        buoy = self.get_buoy(buoy_id)
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
        buoy = self.get_buoy(buoy_id)
        if buoy is None:
            return None
        return BuoySnapshot(
            buoy_id=buoy.id,
            name=buoy.name,
            latitude=buoy.latitude,
            longitude=buoy.longitude,
            status=buoy.status,
            last_seen_at=buoy.last_seen_at,
            created_at=buoy.created_at,
        )

    def add_location(self, reading: LocationTelemetrySnapshot) -> BuoyLocationReadingEntity:
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None:
            buoy.latitude = reading.latitude
            buoy.longitude = reading.longitude
            self.db.commit()
            self.db.refresh(buoy)
        return entity

    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        query = (
            select(BuoyLocationReadingEntity)
            .where(BuoyLocationReadingEntity.buoy_id == buoy_id)
            .order_by(BuoyLocationReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if since is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at >= since)
        if until is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at <= until)
        return [
            LocationTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                latitude=entity.latitude,
                longitude=entity.longitude,
                measured_at=entity.measured_at,
                altitude_meters=entity.altitude_meters,
                speed_mps=entity.speed_mps,
                hdop=entity.hdop,
                satellites=entity.satellites,
                device_id=entity.device_id,
            )
            for entity in self.db.scalars(query).all()
        ]

    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        query = select(BuoyLocationReadingEntity).order_by(
            BuoyLocationReadingEntity.measured_at.desc()
        ).limit(limit)
        if since is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at >= since)
        if until is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at <= until)
        return [
            LocationTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                latitude=entity.latitude,
                longitude=entity.longitude,
                measured_at=entity.measured_at,
                altitude_meters=entity.altitude_meters,
                speed_mps=entity.speed_mps,
                hdop=entity.hdop,
                satellites=entity.satellites,
                device_id=entity.device_id,
            )
            for entity in self.db.scalars(query).all()
        ]

    def get_buoy(self, buoy_id: str) -> BuoyEntity | None:
        return self.db.get(BuoyEntity, buoy_id)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.get_buoy(buoy_id) is not None

    def list_buoys(self) -> list[BuoyEntity]:
        return list(self.db.scalars(select(BuoyEntity).order_by(BuoyEntity.created_at)).all())

    def list_buoy_activity(self) -> list[BuoyActivitySnapshot]:
        return [
            BuoyActivitySnapshot(
                buoy_id=buoy.id,
                name=buoy.name,
                status=buoy.status,
                last_seen_at=buoy.last_seen_at,
            )
            for buoy in self.list_buoys()
        ]

    def list_buoy_identities(self) -> list[BuoyIdentitySnapshot]:
        return [
            BuoyIdentitySnapshot(buoy_id=entity.id, name=entity.name)
            for entity in self.db.scalars(
                select(BuoyEntity).order_by(BuoyEntity.created_at)
            ).all()
        ]

    def create_device(
        self, buoy_id: str, device: DeviceRegistrationCommand
    ) -> DeviceEntity:
        entity = DeviceEntity(
            device_id=device.device_id,
            buoy_id=buoy_id,
            sensor_channel=device.sensor_channel,
            firmware_version=device.firmware_version,
            registered_at=datetime.now(timezone.utc),
        )
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if self.get_device(device.device_id) is not None or any(
                existing.sensor_channel == device.sensor_channel
                for existing in self.list_devices(buoy_id)
            ):
                raise DeviceRegistrationConflict(
                    "Device or sensor channel already registered"
                ) from None
            raise
        self.db.refresh(entity)
        return entity

    def list_devices(self, buoy_id: str) -> list[DeviceEntity]:
        query = select(DeviceEntity).where(DeviceEntity.buoy_id == buoy_id).order_by(DeviceEntity.sensor_channel)
        return list(self.db.scalars(query).all())

    def get_device(self, device_id: str) -> DeviceEntity | None:
        return self.db.get(DeviceEntity, device_id)

    def mark_device_seen(self, device: DeviceEntity, seen_at: datetime) -> DeviceEntity:
        if device.last_seen_at is None or seen_at > device.last_seen_at:
            device.last_seen_at = seen_at
            self.db.commit()
            self.db.refresh(device)
        return device

    def update_device_status(
        self, buoy_id: str, device_id: str, update: DeviceStatusCommand
    ) -> DeviceEntity | None:
        device = self.db.get(DeviceEntity, device_id)
        if device is None or device.buoy_id != buoy_id:
            return None
        device.status = update.status
        self.db.commit()
        self.db.refresh(device)
        return device

    def add_temperature(
        self, reading: TemperatureTelemetrySnapshot
    ) -> TemperatureTelemetrySnapshot:
        entity = TemperatureReadingEntity(
            buoy_id=reading.buoy_id,
            temperature_celsius=reading.temperature_celsius,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
            self.db.refresh(buoy)
        return TemperatureTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            temperature_celsius=entity.temperature_celsius,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        query = (
            select(TemperatureReadingEntity)
            .where(TemperatureReadingEntity.buoy_id == buoy_id)
            .order_by(TemperatureReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(TemperatureReadingEntity.sensor_channel == sensor_channel)
        return [
            TemperatureTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                temperature_celsius=entity.temperature_celsius,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_temperature(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TemperatureTelemetrySnapshot | None:
        readings = self.list_temperatures(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_pressure(
        self, reading: PressureTelemetrySnapshot
    ) -> PressureTelemetrySnapshot:
        entity = PressureReadingEntity(
            buoy_id=reading.buoy_id,
            pressure_kpa=reading.pressure_kpa,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return PressureTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            pressure_kpa=entity.pressure_kpa,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PressureTelemetrySnapshot]:
        query = (
            select(PressureReadingEntity)
            .where(PressureReadingEntity.buoy_id == buoy_id)
            .order_by(PressureReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(PressureReadingEntity.sensor_channel == sensor_channel)
        return [
            PressureTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                pressure_kpa=entity.pressure_kpa,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_pressure(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> PressureReadingEntity | None:
        readings = self.list_pressures(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_salinity(
        self, reading: SalinityTelemetrySnapshot
    ) -> SalinityTelemetrySnapshot:
        entity = SalinityReadingEntity(
            buoy_id=reading.buoy_id,
            salinity_psu=reading.salinity_psu,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return SalinityTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            salinity_psu=entity.salinity_psu,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        query = (
            select(SalinityReadingEntity)
            .where(SalinityReadingEntity.buoy_id == buoy_id)
            .order_by(SalinityReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(SalinityReadingEntity.sensor_channel == sensor_channel)
        return [
            SalinityTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                salinity_psu=entity.salinity_psu,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_salinity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> SalinityTelemetrySnapshot | None:
        readings = self.list_salinity(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
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

    def add_ambient_light(
        self, reading: AmbientLightTelemetrySnapshot
    ) -> AmbientLightTelemetrySnapshot:
        entity = AmbientLightReadingEntity(
            buoy_id=reading.buoy_id,
            illuminance_lux=reading.illuminance_lux,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return AmbientLightTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            illuminance_lux=entity.illuminance_lux,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        query = (
            select(AmbientLightReadingEntity)
            .where(AmbientLightReadingEntity.buoy_id == buoy_id)
            .order_by(AmbientLightReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(AmbientLightReadingEntity.sensor_channel == sensor_channel)
        return [
            AmbientLightTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                illuminance_lux=entity.illuminance_lux,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_ambient_light(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> AmbientLightTelemetrySnapshot | None:
        readings = self.list_ambient_light(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_wind(self, reading: WindTelemetrySnapshot) -> WindTelemetrySnapshot:
        entity = WindReadingEntity(
            buoy_id=reading.buoy_id,
            wind_speed_mps=reading.wind_speed_mps,
            wind_direction_degrees=reading.wind_direction_degrees,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return WindTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            wind_speed_mps=entity.wind_speed_mps,
            wind_direction_degrees=entity.wind_direction_degrees,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        query = (
            select(WindReadingEntity)
            .where(WindReadingEntity.buoy_id == buoy_id)
            .order_by(WindReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(WindReadingEntity.sensor_channel == sensor_channel)
        return [
            WindTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                wind_speed_mps=entity.wind_speed_mps,
                wind_direction_degrees=entity.wind_direction_degrees,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_wind(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> WindTelemetrySnapshot | None:
        readings = self.list_wind(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_marine_current(
        self, reading: MarineCurrentTelemetrySnapshot
    ) -> MarineCurrentTelemetrySnapshot:
        entity = MarineCurrentReadingEntity(
            buoy_id=reading.buoy_id,
            current_speed_mps=reading.current_speed_mps,
            current_direction_degrees=reading.current_direction_degrees,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return MarineCurrentTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            current_speed_mps=entity.current_speed_mps,
            current_direction_degrees=entity.current_direction_degrees,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        query = (
            select(MarineCurrentReadingEntity)
            .where(MarineCurrentReadingEntity.buoy_id == buoy_id)
            .order_by(MarineCurrentReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(MarineCurrentReadingEntity.sensor_channel == sensor_channel)
        return [
            MarineCurrentTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                current_speed_mps=entity.current_speed_mps,
                current_direction_degrees=entity.current_direction_degrees,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_marine_current(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> MarineCurrentTelemetrySnapshot | None:
        readings = self.list_marine_current(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None

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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
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
        readings = self.list_turbidity(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
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

    def add_ph(self, reading: PHTelemetrySnapshot) -> PHTelemetrySnapshot:
        entity = PHReadingEntity(
            buoy_id=reading.buoy_id,
            ph=reading.ph,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return PHTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            ph=entity.ph,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PHTelemetrySnapshot]:
        query = (
            select(PHReadingEntity)
            .where(PHReadingEntity.buoy_id == buoy_id)
            .order_by(PHReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(PHReadingEntity.sensor_channel == sensor_channel)
        return [
            PHTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                ph=entity.ph,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_ph(self, buoy_id: str, sensor_channel: str = "A") -> PHTelemetrySnapshot | None:
        readings = self.list_ph(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_conductivity(
        self, reading: ConductivityTelemetrySnapshot
    ) -> ConductivityTelemetrySnapshot:
        entity = ConductivityReadingEntity(
            buoy_id=reading.buoy_id,
            conductivity_us_cm=reading.conductivity_us_cm,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return ConductivityTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            conductivity_us_cm=entity.conductivity_us_cm,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ConductivityTelemetrySnapshot]:
        query = (
            select(ConductivityReadingEntity)
            .where(ConductivityReadingEntity.buoy_id == buoy_id)
            .order_by(ConductivityReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(
                ConductivityReadingEntity.sensor_channel == sensor_channel
            )
        return [
            ConductivityTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                conductivity_us_cm=entity.conductivity_us_cm,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_conductivity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ConductivityTelemetrySnapshot | None:
        readings = self.list_conductivity(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None

    def add_chlorophyll_a(
        self, reading: ChlorophyllATelemetrySnapshot
    ) -> ChlorophyllATelemetrySnapshot:
        entity = ChlorophyllAReadingEntity(
            buoy_id=reading.buoy_id,
            chlorophyll_a_ug_l=reading.chlorophyll_a_ug_l,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return ChlorophyllATelemetrySnapshot(
            buoy_id=entity.buoy_id,
            chlorophyll_a_ug_l=entity.chlorophyll_a_ug_l,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
        query = (
            select(ChlorophyllAReadingEntity)
            .where(ChlorophyllAReadingEntity.buoy_id == buoy_id)
            .order_by(ChlorophyllAReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(
                ChlorophyllAReadingEntity.sensor_channel == sensor_channel
            )
        return [
            ChlorophyllATelemetrySnapshot(
                buoy_id=entity.buoy_id,
                chlorophyll_a_ug_l=entity.chlorophyll_a_ug_l,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_chlorophyll_a(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ChlorophyllATelemetrySnapshot | None:
        readings = self.list_chlorophyll_a(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None

    def add_rainfall(self, reading: RainfallTelemetrySnapshot) -> RainfallReadingEntity:
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return entity

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[RainfallReadingEntity]:
        query = (
            select(RainfallReadingEntity)
            .where(RainfallReadingEntity.buoy_id == buoy_id)
            .order_by(RainfallReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(RainfallReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_rainfall(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> RainfallReadingEntity | None:
        readings = self.list_rainfall(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_humidity(self, reading: HumidityTelemetrySnapshot) -> HumidityReadingEntity:
        entity = HumidityReadingEntity(
            buoy_id=reading.buoy_id,
            humidity_percent=reading.humidity_percent,
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return entity

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[HumidityReadingEntity]:
        query = select(HumidityReadingEntity).where(HumidityReadingEntity.buoy_id == buoy_id).order_by(HumidityReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(HumidityReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_humidity(self, buoy_id: str, sensor_channel: str = "A") -> HumidityReadingEntity | None:
        readings = self.list_humidity(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_air_temperature(self, reading: AirTemperatureTelemetrySnapshot) -> AirTemperatureReadingEntity:
        entity = AirTemperatureReadingEntity(
            buoy_id=reading.buoy_id, air_temperature_celsius=reading.air_temperature_celsius,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return entity

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AirTemperatureReadingEntity]:
        query = select(AirTemperatureReadingEntity).where(AirTemperatureReadingEntity.buoy_id == buoy_id).order_by(AirTemperatureReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(AirTemperatureReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_air_temperature(self, buoy_id: str, sensor_channel: str = "A") -> AirTemperatureReadingEntity | None:
        readings = self.list_air_temperature(buoy_id, 1, sensor_channel)
        return readings[0] if readings else None

    def add_atmospheric_pressure(self, reading: AtmosphericPressureTelemetrySnapshot) -> AtmosphericPressureReadingEntity:
        entity = AtmosphericPressureReadingEntity(
            buoy_id=reading.buoy_id, atmospheric_pressure_kpa=reading.atmospheric_pressure_kpa,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return entity

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AtmosphericPressureReadingEntity]:
        query = select(AtmosphericPressureReadingEntity).where(AtmosphericPressureReadingEntity.buoy_id == buoy_id).order_by(AtmosphericPressureReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(AtmosphericPressureReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_atmospheric_pressure(self, buoy_id: str, sensor_channel: str = "A") -> AtmosphericPressureReadingEntity | None:
        readings = self.list_atmospheric_pressure(buoy_id, 1, sensor_channel)
        return readings[0] if readings else None

    def add_acoustic_altimeter(self, reading: AcousticAltimeterTelemetrySnapshot) -> AcousticAltimeterReadingEntity:
        entity = AcousticAltimeterReadingEntity(
            buoy_id=reading.buoy_id, depth_meters=reading.depth_meters,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return entity

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AcousticAltimeterReadingEntity]:
        query = select(AcousticAltimeterReadingEntity).where(AcousticAltimeterReadingEntity.buoy_id == buoy_id).order_by(AcousticAltimeterReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(AcousticAltimeterReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def add_underwater_acoustic(self, reading: UnderwaterAcousticTelemetrySnapshot) -> UnderwaterAcousticReadingEntity:
        entity = UnderwaterAcousticReadingEntity(
            buoy_id=reading.buoy_id, echo_intensity_db=reading.echo_intensity_db,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return entity

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[UnderwaterAcousticReadingEntity]:
        query = select(UnderwaterAcousticReadingEntity).where(UnderwaterAcousticReadingEntity.buoy_id == buoy_id).order_by(UnderwaterAcousticReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(UnderwaterAcousticReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def add_battery(self, reading: BatteryTelemetrySnapshot) -> BatteryReadingEntity:
        entity = BatteryReadingEntity(
            buoy_id=reading.buoy_id,
            device_id=reading.device_id,
            battery_percent=reading.battery_percent,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and _is_newer(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return BatteryTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            battery_percent=entity.battery_percent,
            device_id=entity.device_id,
            measured_at=entity.measured_at,
        )

    def add_sensor_health_check(self, health: SensorHealth) -> SensorHealthCheckEntity:
        entity = SensorHealthCheckEntity(
            buoy_id=health.buoy_id,
            status=health.status,
            temperature_delta_celsius=health.temperature_delta_celsius,
            pressure_delta_kpa=health.pressure_delta_kpa,
            salinity_delta_psu=health.salinity_delta_psu,
            imu_acceleration_delta_mps2=health.imu_acceleration_delta_mps2,
            ambient_light_delta_lux=health.ambient_light_delta_lux,
            wind_speed_delta_mps=health.wind_speed_delta_mps,
            wind_direction_delta_degrees=health.wind_direction_delta_degrees,
            marine_current_speed_delta_mps=health.marine_current_speed_delta_mps,
            marine_current_direction_delta_degrees=health.marine_current_direction_delta_degrees,
            turbidity_delta_ntu=health.turbidity_delta_ntu,
            dissolved_oxygen_delta_mg_l=health.dissolved_oxygen_delta_mg_l,
            ph_delta=health.ph_delta,
            conductivity_delta_us_cm=health.conductivity_delta_us_cm,
            chlorophyll_a_delta_ug_l=health.chlorophyll_a_delta_ug_l,
            rainfall_delta_mm_h=health.rainfall_delta_mm_h,
            humidity_delta_percent=health.humidity_delta_percent,
            air_temperature_delta_celsius=health.air_temperature_delta_celsius,
            atmospheric_pressure_delta_kpa=health.atmospheric_pressure_delta_kpa,
            acoustic_altimeter_delta_meters=health.acoustic_altimeter_delta_meters,
            underwater_acoustic_delta_db=health.underwater_acoustic_delta_db,
            degraded_sensors=health.degraded_sensors,
            missing_sensors=health.missing_sensors,
            decisions=health.decisions,
            checked_at=health.checked_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckEntity]:
        query = (
            select(SensorHealthCheckEntity)
            .where(SensorHealthCheckEntity.buoy_id == buoy_id)
            .order_by(SensorHealthCheckEntity.checked_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())

    def latest_battery(
        self, buoy_id: str, device_id: str | None = None
    ) -> BatteryReadingEntity | None:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(1)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        entity = self.db.scalars(query).first()
        if entity is None:
            return None
        return BatteryTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            battery_percent=entity.battery_percent,
            device_id=entity.device_id,
            measured_at=entity.measured_at,
        )

    def list_batteries(
        self, buoy_id: str, limit: int, device_id: str | None = None
    ) -> list[BatteryTelemetrySnapshot]:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        return [
            BatteryTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                battery_percent=entity.battery_percent,
                device_id=entity.device_id,
                measured_at=entity.measured_at,
            )
            for entity in self.db.scalars(query).all()
        ]

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        counts = {"good": 0, "suspect": 0, "invalid": 0}
        for entity in (
            TemperatureReadingEntity,
            PressureReadingEntity,
            SalinityReadingEntity,
        ):
            query = (
                select(entity.quality, func.count())
                .where(entity.buoy_id == buoy_id)
                .group_by(entity.quality)
            )
            for quality, count in self.db.execute(query):
                if quality in counts:
                    counts[quality] += count
        return counts

    def _temperature_alert_snapshot(
        self, entity: TemperatureAlertEntity
    ) -> TemperatureAlertSnapshot:
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
        return self._temperature_alert_snapshot(entity) if entity is not None else None

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
        return self._temperature_alert_snapshot(entity)

    def list_alerts(self, status: str = "open") -> list[TemperatureAlertSnapshot]:
        query = select(TemperatureAlertEntity).where(
            TemperatureAlertEntity.status == status
        ).order_by(TemperatureAlertEntity.created_at.desc())
        return [self._temperature_alert_snapshot(entity) for entity in self.db.scalars(query).all()]

    def resolve_alert(self, alert_id: int) -> TemperatureAlertSnapshot | None:
        alert = self.db.get(TemperatureAlertEntity, alert_id)
        if alert is None:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.now(alert.created_at.tzinfo)
        self.db.commit()
        self.db.refresh(alert)
        return self._temperature_alert_snapshot(alert)
