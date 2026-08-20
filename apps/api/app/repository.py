from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .entities import (
    BuoyEntity,
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
    ImuReading,
    AmbientLightReading,
    WindReading,
    MarineCurrentReading,
    TurbidityReading,
    DissolvedOxygenReading,
    PHReading,
    ConductivityReading,
    ChlorophyllAReading,
    SensorHealth,
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
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def add_imu(self, reading: ImuReading) -> ImuReadingEntity:
        entity = ImuReadingEntity(
            buoy_id=reading.buoy_id,
            acceleration_x_mps2=reading.acceleration_x_mps2,
            acceleration_y_mps2=reading.acceleration_y_mps2,
            acceleration_z_mps2=reading.acceleration_z_mps2,
            angular_velocity_x_dps=reading.angular_velocity_x_dps,
            angular_velocity_y_dps=reading.angular_velocity_y_dps,
            angular_velocity_z_dps=reading.angular_velocity_z_dps,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ImuReadingEntity]:
        query = (
            select(ImuReadingEntity)
            .where(ImuReadingEntity.buoy_id == buoy_id)
            .order_by(ImuReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(ImuReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_imu(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ImuReadingEntity | None:
        readings = self.list_imu(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_ambient_light(
        self, reading: AmbientLightReading
    ) -> AmbientLightReadingEntity:
        entity = AmbientLightReadingEntity(
            buoy_id=reading.buoy_id,
            illuminance_lux=reading.illuminance_lux,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AmbientLightReadingEntity]:
        query = (
            select(AmbientLightReadingEntity)
            .where(AmbientLightReadingEntity.buoy_id == buoy_id)
            .order_by(AmbientLightReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(AmbientLightReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_ambient_light(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> AmbientLightReadingEntity | None:
        readings = self.list_ambient_light(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_wind(self, reading: WindReading) -> WindReadingEntity:
        entity = WindReadingEntity(
            buoy_id=reading.buoy_id,
            wind_speed_mps=reading.wind_speed_mps,
            wind_direction_degrees=reading.wind_direction_degrees,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[WindReadingEntity]:
        query = (
            select(WindReadingEntity)
            .where(WindReadingEntity.buoy_id == buoy_id)
            .order_by(WindReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(WindReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_wind(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> WindReadingEntity | None:
        readings = self.list_wind(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_marine_current(
        self, reading: MarineCurrentReading
    ) -> MarineCurrentReadingEntity:
        entity = MarineCurrentReadingEntity(
            buoy_id=reading.buoy_id,
            current_speed_mps=reading.current_speed_mps,
            current_direction_degrees=reading.current_direction_degrees,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[MarineCurrentReadingEntity]:
        query = (
            select(MarineCurrentReadingEntity)
            .where(MarineCurrentReadingEntity.buoy_id == buoy_id)
            .order_by(MarineCurrentReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(MarineCurrentReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_marine_current(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> MarineCurrentReadingEntity | None:
        readings = self.list_marine_current(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None

    def add_turbidity(self, reading: TurbidityReading) -> TurbidityReadingEntity:
        entity = TurbidityReadingEntity(
            buoy_id=reading.buoy_id,
            turbidity_ntu=reading.turbidity_ntu,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TurbidityReadingEntity]:
        query = (
            select(TurbidityReadingEntity)
            .where(TurbidityReadingEntity.buoy_id == buoy_id)
            .order_by(TurbidityReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(TurbidityReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_turbidity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TurbidityReadingEntity | None:
        readings = self.list_turbidity(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_dissolved_oxygen(
        self, reading: DissolvedOxygenReading
    ) -> DissolvedOxygenReadingEntity:
        entity = DissolvedOxygenReadingEntity(
            buoy_id=reading.buoy_id,
            dissolved_oxygen_mg_l=reading.dissolved_oxygen_mg_l,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[DissolvedOxygenReadingEntity]:
        query = (
            select(DissolvedOxygenReadingEntity)
            .where(DissolvedOxygenReadingEntity.buoy_id == buoy_id)
            .order_by(DissolvedOxygenReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(DissolvedOxygenReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_dissolved_oxygen(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> DissolvedOxygenReadingEntity | None:
        readings = self.list_dissolved_oxygen(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None

    def add_ph(self, reading: PHReading) -> PHReadingEntity:
        entity = PHReadingEntity(
            buoy_id=reading.buoy_id,
            ph=reading.ph,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PHReadingEntity]:
        query = (
            select(PHReadingEntity)
            .where(PHReadingEntity.buoy_id == buoy_id)
            .order_by(PHReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if sensor_channel is not None:
            query = query.where(PHReadingEntity.sensor_channel == sensor_channel)
        return list(self.db.scalars(query).all())

    def latest_ph(self, buoy_id: str, sensor_channel: str = "A") -> PHReadingEntity | None:
        readings = self.list_ph(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_conductivity(
        self, reading: ConductivityReading
    ) -> ConductivityReadingEntity:
        entity = ConductivityReadingEntity(
            buoy_id=reading.buoy_id,
            conductivity_us_cm=reading.conductivity_us_cm,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ConductivityReadingEntity]:
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
        return list(self.db.scalars(query).all())

    def latest_conductivity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ConductivityReadingEntity | None:
        readings = self.list_conductivity(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
        return readings[0] if readings else None

    def add_chlorophyll_a(
        self, reading: ChlorophyllAReading
    ) -> ChlorophyllAReadingEntity:
        entity = ChlorophyllAReadingEntity(
            buoy_id=reading.buoy_id,
            chlorophyll_a_ug_l=reading.chlorophyll_a_ug_l,
            sensor_channel=reading.sensor_channel,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version,
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

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ChlorophyllAReadingEntity]:
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
        return list(self.db.scalars(query).all())

    def latest_chlorophyll_a(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ChlorophyllAReadingEntity | None:
        readings = self.list_chlorophyll_a(
            buoy_id, limit=1, sensor_channel=sensor_channel
        )
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
