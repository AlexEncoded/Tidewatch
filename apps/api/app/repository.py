from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .entities import (
    BuoyEntity,
    BuoyLocationReadingEntity,
    BatteryReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    TemperatureAlertEntity,
    TemperatureReadingEntity,
)
from .models import (
    Buoy,
    BuoyStatusUpdate,
    BuoyLocationUpdate,
    BuoyLocationReading,
    PressureReading,
    SalinityReading,
    BatteryReading,
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

    def update_location(
        self, buoy_id: str, update: BuoyLocationUpdate
    ) -> BuoyEntity | None:
        buoy = self.get_buoy(buoy_id)
        if buoy is None:
            return None
        self.add_location(
            BuoyLocationReading(
                buoy_id=buoy_id,
                latitude=update.latitude,
                longitude=update.longitude,
            )
        )
        return self.get_buoy(buoy_id)

    def add_location(self, reading: BuoyLocationReading) -> BuoyLocationReadingEntity:
        entity = BuoyLocationReadingEntity(
            buoy_id=reading.buoy_id,
            latitude=reading.latitude,
            longitude=reading.longitude,
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
    ) -> list[BuoyLocationReadingEntity]:
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
        return list(self.db.scalars(query).all())

    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[BuoyLocationReadingEntity]:
        query = select(BuoyLocationReadingEntity).order_by(
            BuoyLocationReadingEntity.measured_at.desc()
        ).limit(limit)
        if since is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at >= since)
        if until is not None:
            query = query.where(BuoyLocationReadingEntity.measured_at <= until)
        return list(self.db.scalars(query).all())

    def get_buoy(self, buoy_id: str) -> BuoyEntity | None:
        return self.db.get(BuoyEntity, buoy_id)

    def list_buoys(self) -> list[BuoyEntity]:
        return list(self.db.scalars(select(BuoyEntity).order_by(BuoyEntity.created_at)).all())

    def add_temperature(self, reading: TemperatureReading) -> TemperatureReadingEntity:
        entity = TemperatureReadingEntity(
            buoy_id=reading.buoy_id,
            temperature_celsius=reading.temperature_celsius,
            sensor_channel=reading.sensor_channel,
            quality=reading.quality,
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

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TemperatureReadingEntity]:
        query = (
            select(TemperatureReadingEntity)
            .where(TemperatureReadingEntity.buoy_id == buoy_id)
            .order_by(TemperatureReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(TemperatureReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_temperature(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TemperatureReadingEntity | None:
        readings = self.list_temperatures(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_pressure(self, reading: PressureReading) -> PressureReadingEntity:
        entity = PressureReadingEntity(
            buoy_id=reading.buoy_id,
            pressure_kpa=reading.pressure_kpa,
            sensor_channel=reading.sensor_channel,
            quality=reading.quality,
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

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PressureReadingEntity]:
        query = (
            select(PressureReadingEntity)
            .where(PressureReadingEntity.buoy_id == buoy_id)
            .order_by(PressureReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(PressureReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_pressure(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> PressureReadingEntity | None:
        readings = self.list_pressures(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_salinity(self, reading: SalinityReading) -> SalinityReadingEntity:
        entity = SalinityReadingEntity(
            buoy_id=reading.buoy_id,
            salinity_psu=reading.salinity_psu,
            sensor_channel=reading.sensor_channel,
            quality=reading.quality,
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

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[SalinityReadingEntity]:
        query = (
            select(SalinityReadingEntity)
            .where(SalinityReadingEntity.buoy_id == buoy_id)
            .order_by(SalinityReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(SalinityReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_salinity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> SalinityReadingEntity | None:
        readings = self.list_salinity(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_battery(self, reading: BatteryReading) -> BatteryReadingEntity:
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
        if buoy is not None and (
            buoy.last_seen_at is None or reading.measured_at > buoy.last_seen_at
        ):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return entity

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
        return self.db.scalars(query).first()

    def list_batteries(
        self, buoy_id: str, limit: int, device_id: str | None = None
    ) -> list[BatteryReadingEntity]:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        return list(self.db.scalars(query).all())

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
