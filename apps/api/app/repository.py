from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .entities import (
    BuoyEntity,
    DeviceEntity,
    SensorHealthCheckEntity,
    BuoyLocationReadingEntity,
    BatteryReadingEntity,
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
    TemperatureReadingEntity,
)
from .domain.buoy import (
    BuoySnapshot,
)
from .domain.devices import DeviceSnapshot
from .domain.sensor_health import (
    SensorHealthCheckSnapshot,
    SensorHealthSnapshot as DomainSensorHealthSnapshot,
)
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
from .persistence_mappers import (
    buoy_snapshot as _buoy_snapshot,
    sensor_health_check_snapshot as _sensor_health_check_snapshot,
)
from .device_repository import DeviceRepository
from .buoy_location_repository import BuoyLocationRepository
from .buoy_registry_repository import BuoyRegistryRepository
from .temperature_repository import TemperatureRepository
from .pressure_repository import PressureRepository
from .salinity_repository import SalinityRepository
from .imu_repository import ImuRepository
from .ambient_light_repository import AmbientLightRepository
from .wind_repository import WindRepository
from .persistence_utils import is_newer_timestamp


class BuoyRepository:
    """Legacy aggregate adapter retained while use cases migrate by context."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.devices = DeviceRepository(db)
        self.locations = BuoyLocationRepository(db)
        self.registry = BuoyRegistryRepository(db)
        self.temperature = TemperatureRepository(db)
        self.pressure = PressureRepository(db)
        self.salinity = SalinityRepository(db)
        self.imu = ImuRepository(db)
        self.ambient_light = AmbientLightRepository(db)
        self.wind = WindRepository(db)

    def get_device(self, device_id: str) -> DeviceEntity | None:
        """Delegate battery ownership lookups to the device persistence adapter."""
        return self.devices.get_device(device_id)

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        """Delegate device snapshot reads required by battery ingestion."""
        return self.devices.get_device_snapshot(device_id)

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        """Delegate device snapshots required by legacy maintenance queries."""
        return self.devices.list_device_snapshots(buoy_id)

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        """Delegate battery-ingestion heartbeats to the device adapter."""
        return self.devices.mark_device_seen_by_id(device_id, seen_at)

    def add_location(self, reading: LocationTelemetrySnapshot) -> BuoyLocationReadingEntity:
        return self.locations.add_location(reading)

    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_locations(buoy_id, limit, since, until)

    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_all_locations(limit, since, until)

    def get_buoy(self, buoy_id: str) -> BuoyEntity | None:
        return self.registry.get_buoy(buoy_id)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def list_buoy_snapshots(self) -> list[BuoySnapshot]:
        return self.registry.list_buoy_snapshots()

    def add_temperature(
        self, reading: TemperatureTelemetrySnapshot
    ) -> TemperatureTelemetrySnapshot:
        return self.temperature.add_temperature(reading)

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        return self.temperature.list_temperatures(buoy_id, limit, sensor_channel)

    def latest_temperature(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TemperatureTelemetrySnapshot | None:
        return self.temperature.latest_temperature(buoy_id, sensor_channel)

    def add_pressure(
        self, reading: PressureTelemetrySnapshot
    ) -> PressureTelemetrySnapshot:
        return self.pressure.add_pressure(reading)

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PressureTelemetrySnapshot]:
        return self.pressure.list_pressures(buoy_id, limit, sensor_channel)

    def latest_pressure(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> PressureReadingEntity | None:
        return self.pressure.latest_pressure(buoy_id, sensor_channel)

    def add_salinity(
        self, reading: SalinityTelemetrySnapshot
    ) -> SalinityTelemetrySnapshot:
        return self.salinity.add_salinity(reading)

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        return self.salinity.list_salinity(buoy_id, limit, sensor_channel)

    def latest_salinity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> SalinityTelemetrySnapshot | None:
        return self.salinity.latest_salinity(buoy_id, sensor_channel)

    def add_imu(self, reading: ImuTelemetrySnapshot) -> ImuTelemetrySnapshot:
        return self.imu.add_imu(reading)

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        return self.imu.list_imu(buoy_id, limit, sensor_channel)

    def latest_imu(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ImuTelemetrySnapshot | None:
        return self.imu.latest_imu(buoy_id, sensor_channel)

    def add_ambient_light(
        self, reading: AmbientLightTelemetrySnapshot
    ) -> AmbientLightTelemetrySnapshot:
        return self.ambient_light.add_ambient_light(reading)

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        return self.ambient_light.list_ambient_light(buoy_id, limit, sensor_channel)

    def latest_ambient_light(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> AmbientLightTelemetrySnapshot | None:
        return self.ambient_light.latest_ambient_light(buoy_id, sensor_channel)

    def add_wind(self, reading: WindTelemetrySnapshot) -> WindTelemetrySnapshot:
        return self.wind.add_wind(reading)

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        return self.wind.list_wind(buoy_id, limit, sensor_channel)

    def latest_wind(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> WindTelemetrySnapshot | None:
        return self.wind.latest_wind(buoy_id, sensor_channel)

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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
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
            query = query.where(RainfallReadingEntity.sensor_channel == sensor_channel)
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
        readings = self.list_rainfall(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_humidity(
        self, reading: HumidityTelemetrySnapshot
    ) -> HumidityTelemetrySnapshot:
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
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return HumidityTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            humidity_percent=entity.humidity_percent,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[HumidityTelemetrySnapshot]:
        query = select(HumidityReadingEntity).where(HumidityReadingEntity.buoy_id == buoy_id).order_by(HumidityReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(HumidityReadingEntity.sensor_channel == sensor_channel)
        return [
            HumidityTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                humidity_percent=entity.humidity_percent,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_humidity(self, buoy_id: str, sensor_channel: str = "A") -> HumidityTelemetrySnapshot | None:
        readings = self.list_humidity(buoy_id, limit=1, sensor_channel=sensor_channel)
        return readings[0] if readings else None

    def add_air_temperature(
        self, reading: AirTemperatureTelemetrySnapshot
    ) -> AirTemperatureTelemetrySnapshot:
        entity = AirTemperatureReadingEntity(
            buoy_id=reading.buoy_id, air_temperature_celsius=reading.air_temperature_celsius,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return AirTemperatureTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            air_temperature_celsius=entity.air_temperature_celsius,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AirTemperatureTelemetrySnapshot]:
        query = select(AirTemperatureReadingEntity).where(AirTemperatureReadingEntity.buoy_id == buoy_id).order_by(AirTemperatureReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(AirTemperatureReadingEntity.sensor_channel == sensor_channel)
        return [
            AirTemperatureTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                air_temperature_celsius=entity.air_temperature_celsius,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_air_temperature(self, buoy_id: str, sensor_channel: str = "A") -> AirTemperatureTelemetrySnapshot | None:
        readings = self.list_air_temperature(buoy_id, 1, sensor_channel)
        return readings[0] if readings else None

    def add_atmospheric_pressure(
        self, reading: AtmosphericPressureTelemetrySnapshot
    ) -> AtmosphericPressureTelemetrySnapshot:
        entity = AtmosphericPressureReadingEntity(
            buoy_id=reading.buoy_id, atmospheric_pressure_kpa=reading.atmospheric_pressure_kpa,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return AtmosphericPressureTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            atmospheric_pressure_kpa=entity.atmospheric_pressure_kpa,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AtmosphericPressureTelemetrySnapshot]:
        query = select(AtmosphericPressureReadingEntity).where(AtmosphericPressureReadingEntity.buoy_id == buoy_id).order_by(AtmosphericPressureReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(AtmosphericPressureReadingEntity.sensor_channel == sensor_channel)
        return [
            AtmosphericPressureTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                atmospheric_pressure_kpa=entity.atmospheric_pressure_kpa,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def latest_atmospheric_pressure(self, buoy_id: str, sensor_channel: str = "A") -> AtmosphericPressureTelemetrySnapshot | None:
        readings = self.list_atmospheric_pressure(buoy_id, 1, sensor_channel)
        return readings[0] if readings else None

    def add_acoustic_altimeter(
        self, reading: AcousticAltimeterTelemetrySnapshot
    ) -> AcousticAltimeterTelemetrySnapshot:
        entity = AcousticAltimeterReadingEntity(
            buoy_id=reading.buoy_id, depth_meters=reading.depth_meters,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
        return AcousticAltimeterTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            depth_meters=entity.depth_meters,
            measured_at=entity.measured_at,
            sensor_channel=entity.sensor_channel,
            device_id=entity.device_id,
            sensor_id=entity.sensor_id,
            firmware_version=entity.firmware_version,
            quality=entity.quality,
        )

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AcousticAltimeterTelemetrySnapshot]:
        query = select(AcousticAltimeterReadingEntity).where(AcousticAltimeterReadingEntity.buoy_id == buoy_id).order_by(AcousticAltimeterReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(AcousticAltimeterReadingEntity.sensor_channel == sensor_channel)
        return [
            AcousticAltimeterTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                depth_meters=entity.depth_meters,
                measured_at=entity.measured_at,
                sensor_channel=entity.sensor_channel,
                device_id=entity.device_id,
                sensor_id=entity.sensor_id,
                firmware_version=entity.firmware_version,
                quality=entity.quality,
            )
            for entity in self.db.scalars(query).all()
        ]

    def add_underwater_acoustic(
        self, reading: UnderwaterAcousticTelemetrySnapshot
    ) -> UnderwaterAcousticTelemetrySnapshot:
        entity = UnderwaterAcousticReadingEntity(
            buoy_id=reading.buoy_id, echo_intensity_db=reading.echo_intensity_db,
            sensor_channel=reading.sensor_channel, device_id=reading.device_id,
            sensor_id=reading.sensor_id,
            firmware_version=reading.firmware_version, quality=reading.quality,
            measured_at=reading.measured_at,
        )
        self.db.add(entity); self.db.commit(); self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at; self.db.commit()
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

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[UnderwaterAcousticTelemetrySnapshot]:
        query = select(UnderwaterAcousticReadingEntity).where(UnderwaterAcousticReadingEntity.buoy_id == buoy_id).order_by(UnderwaterAcousticReadingEntity.measured_at.desc()).limit(limit)
        if sensor_channel is not None:
            query = query.where(UnderwaterAcousticReadingEntity.sensor_channel == sensor_channel)
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

    def add_battery(self, reading: BatteryTelemetrySnapshot) -> BatteryReadingEntity:
        entity = BatteryReadingEntity(
            buoy_id=reading.buoy_id,
            device_id=reading.device_id,
            physical_device_id=reading.physical_device_id,
            battery_percent=reading.battery_percent,
            measured_at=reading.measured_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        buoy = self.get_buoy(reading.buoy_id)
        if buoy is not None and is_newer_timestamp(reading.measured_at, buoy.last_seen_at):
            buoy.last_seen_at = reading.measured_at
            self.db.commit()
        return BatteryTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            battery_percent=entity.battery_percent,
            device_id=entity.device_id,
            measured_at=entity.measured_at,
            physical_device_id=entity.physical_device_id,
        )

    def add_sensor_health_check(
        self, health: DomainSensorHealthSnapshot
    ) -> SensorHealthCheckSnapshot:
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
        return _sensor_health_check_snapshot(entity)

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckSnapshot]:
        query = (
            select(SensorHealthCheckEntity)
            .where(SensorHealthCheckEntity.buoy_id == buoy_id)
            .order_by(SensorHealthCheckEntity.checked_at.desc())
            .limit(limit)
        )
        return [
            _sensor_health_check_snapshot(entity)
            for entity in self.db.scalars(query).all()
        ]

    def latest_battery(
        self,
        buoy_id: str,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> BatteryReadingEntity | None:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(1)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        if physical_device_id is not None:
            query = query.where(
                BatteryReadingEntity.physical_device_id == physical_device_id
            )
        entity = self.db.scalars(query).first()
        if entity is None:
            return None
        return BatteryTelemetrySnapshot(
            buoy_id=entity.buoy_id,
            battery_percent=entity.battery_percent,
            device_id=entity.device_id,
            measured_at=entity.measured_at,
            physical_device_id=entity.physical_device_id,
        )

    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> list[BatteryTelemetrySnapshot]:
        query = (
            select(BatteryReadingEntity)
            .where(BatteryReadingEntity.buoy_id == buoy_id)
            .order_by(BatteryReadingEntity.measured_at.desc())
            .limit(limit)
        )
        if device_id is not None:
            query = query.where(BatteryReadingEntity.device_id == device_id)
        if physical_device_id is not None:
            query = query.where(
                BatteryReadingEntity.physical_device_id == physical_device_id
            )
        return [
            BatteryTelemetrySnapshot(
                buoy_id=entity.buoy_id,
                battery_percent=entity.battery_percent,
                device_id=entity.device_id,
                measured_at=entity.measured_at,
                physical_device_id=entity.physical_device_id,
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
