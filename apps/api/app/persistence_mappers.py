"""Translate persistence entities into immutable application/domain snapshots."""

from .domain.buoy import BuoySnapshot
from .domain.devices import DeviceSnapshot
from .domain.sensor_health import SensorHealthCheckSnapshot
from .entities import BuoyEntity, DeviceEntity
from .sensor_entities import SensorHealthCheckEntity


def sensor_health_check_snapshot(
    entity: SensorHealthCheckEntity,
) -> SensorHealthCheckSnapshot:
    """Map a persisted health evaluation to its domain snapshot."""
    return SensorHealthCheckSnapshot(
        id=entity.id,
        buoy_id=entity.buoy_id,
        status=entity.status,
        checked_at=entity.checked_at,
        temperature_delta_celsius=entity.temperature_delta_celsius,
        pressure_delta_kpa=entity.pressure_delta_kpa,
        salinity_delta_psu=entity.salinity_delta_psu,
        imu_acceleration_delta_mps2=entity.imu_acceleration_delta_mps2,
        ambient_light_delta_lux=entity.ambient_light_delta_lux,
        wind_speed_delta_mps=entity.wind_speed_delta_mps,
        wind_direction_delta_degrees=entity.wind_direction_delta_degrees,
        marine_current_speed_delta_mps=entity.marine_current_speed_delta_mps,
        marine_current_direction_delta_degrees=entity.marine_current_direction_delta_degrees,
        turbidity_delta_ntu=entity.turbidity_delta_ntu,
        dissolved_oxygen_delta_mg_l=entity.dissolved_oxygen_delta_mg_l,
        ph_delta=entity.ph_delta,
        conductivity_delta_us_cm=entity.conductivity_delta_us_cm,
        chlorophyll_a_delta_ug_l=entity.chlorophyll_a_delta_ug_l,
        rainfall_delta_mm_h=entity.rainfall_delta_mm_h,
        humidity_delta_percent=entity.humidity_delta_percent,
        air_temperature_delta_celsius=entity.air_temperature_delta_celsius,
        atmospheric_pressure_delta_kpa=entity.atmospheric_pressure_delta_kpa,
        acoustic_altimeter_delta_meters=entity.acoustic_altimeter_delta_meters,
        underwater_acoustic_delta_db=entity.underwater_acoustic_delta_db,
        degraded_sensors=entity.degraded_sensors,
        missing_sensors=entity.missing_sensors,
        decisions=entity.decisions,
    )


def device_snapshot(entity: DeviceEntity) -> DeviceSnapshot:
    """Map a registered physical-device entity to its domain snapshot."""
    return DeviceSnapshot(
        buoy_id=entity.buoy_id,
        device_id=entity.device_id,
        sensor_channel=entity.sensor_channel,
        registered_at=entity.registered_at,
        firmware_version=entity.firmware_version,
        status=entity.status,
        last_seen_at=entity.last_seen_at,
    )


def buoy_snapshot(entity: BuoyEntity) -> BuoySnapshot:
    """Map a buoy persistence entity to its domain snapshot."""
    return BuoySnapshot(
        buoy_id=entity.id,
        name=entity.name,
        latitude=entity.latitude,
        longitude=entity.longitude,
        status=entity.status,
        last_seen_at=entity.last_seen_at,
        created_at=entity.created_at,
    )
