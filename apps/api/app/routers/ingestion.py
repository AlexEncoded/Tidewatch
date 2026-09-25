"""HTTP route for batch telemetry ingestion."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..application.device_heartbeat import record_device_heartbeat
from ..application.movement_analysis import analyze_movement_for_buoy
from ..application.telemetry_ingestion import (
    build_location_snapshot,
    build_rainfall_snapshot,
    build_chlorophyll_a_snapshot,
    build_conductivity_snapshot,
    build_ph_snapshot,
    build_dissolved_oxygen_snapshot,
    build_imu_snapshot,
    build_marine_current_snapshot,
    build_turbidity_snapshot,
    build_ambient_light_snapshot,
    build_wind_snapshot,
    build_pressure_snapshot,
    build_salinity_snapshot,
    build_temperature_snapshot,
    empty_accepted_reading_counts,
    with_device_provenance,
)
from ..database import get_db
from ..domain.devices import DeviceOwnershipError
from ..metrics import (
    acoustic_altimeter_readings_total, air_temperature_readings_total,
    ambient_light_readings_total, atmospheric_pressure_readings_total,
    battery_device_percent, battery_percent, buoy_last_seen_timestamp_seconds,
    buoy_movement_speed_mps, chlorophyll_a_readings_total,
    conductivity_readings_total,
    current_acoustic_altimeter_depth_meters, current_air_temperature_celsius,
    current_ambient_light_lux, current_atmospheric_pressure_kpa,
    current_chlorophyll_a_ug_l, current_conductivity_us_cm,
    current_dissolved_oxygen_mg_l, current_humidity_percent,
    current_imu_acceleration_mps2, current_imu_angular_velocity_dps,
    current_marine_current_direction_degrees, current_marine_current_speed_mps,
    current_ph, current_pressure_kpa, current_rainfall_mm_h,
    current_salinity_psu, current_temperature_celsius, current_turbidity_ntu,
    current_underwater_acoustic_echo_intensity_db, current_wind_direction_degrees,
    current_wind_speed_mps, device_last_seen_timestamp_seconds,
    current_gnss_altitude_meters, current_gnss_speed_mps,
    current_gnss_hdop, current_gnss_satellites,
    dissolved_oxygen_readings_total, humidity_readings_total, imu_readings_total,
    marine_current_readings_total, ph_readings_total, pressure_readings_total,
    rainfall_readings_total, reading_quality_total, salinity_readings_total,
    temperature_readings_total, turbidity_readings_total,
    underwater_acoustic_readings_total, wind_readings_total,
)
from ..models import (
    AcousticAltimeterReading, AirTemperatureReading,
    AtmosphericPressureReading, BatteryReading,
    HumidityReading,
    TelemetryBatchCreate,
    TelemetryIngestResponse,
    UnderwaterAcousticReading,
)
from ..repository import BuoyRepository


router = APIRouter()


def record_quality_metric(buoy_id: str, sensor_family: str, sensor_channel: str, quality: str) -> None:
    reading_quality_total.labels(
        buoy_id=buoy_id,
        sensor_family=sensor_family,
        sensor_channel=sensor_channel,
        quality=quality,
    ).inc()


@router.post(
    "/api/v1/buoys/{buoy_id}/telemetry",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["telemetry"],
)
def ingest_telemetry(
    buoy_id: str,
    payload: TelemetryBatchCreate,
    db: Session = Depends(get_db),
) -> TelemetryIngestResponse:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    if payload.device_id is not None:
        try:
            device, seen_at = record_device_heartbeat(repository, buoy_id, payload.device_id)
        except DeviceOwnershipError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
        device_last_seen_timestamp_seconds.labels(
            buoy_id=buoy_id,
            device_id=device.device_id,
            sensor_channel=device.sensor_channel,
        ).set(seen_at.timestamp())

    if payload.location is not None:
        location = build_location_snapshot(
            buoy_id, payload.location.model_dump(), payload.device_id
        )
        repository.add_location(location)
        if location.altitude_meters is not None:
            current_gnss_altitude_meters.labels(buoy_id=buoy_id).set(location.altitude_meters)
        if location.speed_mps is not None:
            current_gnss_speed_mps.labels(buoy_id=buoy_id).set(location.speed_mps)
        if location.hdop is not None:
            current_gnss_hdop.labels(buoy_id=buoy_id).set(location.hdop)
        if location.satellites is not None:
            current_gnss_satellites.labels(buoy_id=buoy_id).set(location.satellites)
        movement = analyze_movement_for_buoy(repository, buoy_id, 50)
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(
                movement.average_speed_mps
            )

    accepted = 0
    accepted_by_family = empty_accepted_reading_counts()
    for reading_payload in payload.temperatures:
        reading = build_temperature_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_temperature(reading)
        temperature_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_temperature_celsius.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.temperature_celsius)
        record_quality_metric(buoy_id, "temperature", reading.sensor_channel, reading.quality)
        buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(
            reading.measured_at.timestamp()
        )
        accepted_by_family["temperature"] += 1
        accepted += 1

    for reading_payload in payload.pressures:
        reading = build_pressure_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_pressure(reading)
        pressure_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_pressure_kpa.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.pressure_kpa)
        record_quality_metric(buoy_id, "pressure", reading.sensor_channel, reading.quality)
        accepted_by_family["pressure"] += 1
        accepted += 1

    for reading_payload in payload.salinity:
        reading = build_salinity_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_salinity(reading)
        salinity_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_salinity_psu.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.salinity_psu)
        record_quality_metric(buoy_id, "salinity", reading.sensor_channel, reading.quality)
        accepted_by_family["salinity"] += 1
        accepted += 1

    for reading_payload in payload.imu:
        reading = build_imu_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_imu(reading)
        imu_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        for axis, value in {
            "x": reading.acceleration_x_mps2,
            "y": reading.acceleration_y_mps2,
            "z": reading.acceleration_z_mps2,
        }.items():
            current_imu_acceleration_mps2.labels(
                buoy_id=buoy_id, sensor_channel=reading.sensor_channel, axis=axis
            ).set(value)
        for axis, value in {
            "x": reading.angular_velocity_x_dps,
            "y": reading.angular_velocity_y_dps,
            "z": reading.angular_velocity_z_dps,
        }.items():
            current_imu_angular_velocity_dps.labels(
                buoy_id=buoy_id, sensor_channel=reading.sensor_channel, axis=axis
            ).set(value)
        record_quality_metric(buoy_id, "imu", reading.sensor_channel, reading.quality)
        accepted_by_family["imu"] += 1
        accepted += 1

    for reading_payload in payload.ambient_light:
        reading = build_ambient_light_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_ambient_light(reading)
        ambient_light_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_ambient_light_lux.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.illuminance_lux)
        record_quality_metric(
            buoy_id, "ambient_light", reading.sensor_channel, reading.quality
        )
        accepted_by_family["ambient_light"] += 1
        accepted += 1

    for reading_payload in payload.wind:
        reading = build_wind_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_wind(reading)
        wind_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_wind_speed_mps.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.wind_speed_mps)
        current_wind_direction_degrees.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.wind_direction_degrees)
        record_quality_metric(buoy_id, "wind", reading.sensor_channel, reading.quality)
        accepted_by_family["wind"] += 1
        accepted += 1

    for reading_payload in payload.marine_current:
        reading = build_marine_current_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_marine_current(reading)
        marine_current_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_marine_current_speed_mps.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.current_speed_mps)
        current_marine_current_direction_degrees.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.current_direction_degrees)
        record_quality_metric(
            buoy_id, "marine_current", reading.sensor_channel, reading.quality
        )
        accepted_by_family["marine_current"] += 1
        accepted += 1

    for reading_payload in payload.turbidity:
        reading = build_turbidity_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_turbidity(reading)
        turbidity_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_turbidity_ntu.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.turbidity_ntu)
        record_quality_metric(
            buoy_id, "turbidity", reading.sensor_channel, reading.quality
        )
        accepted_by_family["turbidity"] += 1
        accepted += 1

    for reading_payload in payload.dissolved_oxygen:
        reading = build_dissolved_oxygen_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_dissolved_oxygen(reading)
        dissolved_oxygen_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_dissolved_oxygen_mg_l.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.dissolved_oxygen_mg_l)
        record_quality_metric(
            buoy_id, "dissolved_oxygen", reading.sensor_channel, reading.quality
        )
        accepted_by_family["dissolved_oxygen"] += 1
        accepted += 1

    for reading_payload in payload.ph:
        reading = build_ph_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_ph(reading)
        ph_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_ph.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.ph)
        record_quality_metric(buoy_id, "ph", reading.sensor_channel, reading.quality)
        accepted_by_family["ph"] += 1
        accepted += 1

    for reading_payload in payload.conductivity:
        reading = build_conductivity_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_conductivity(reading)
        conductivity_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_conductivity_us_cm.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.conductivity_us_cm)
        record_quality_metric(
            buoy_id, "conductivity", reading.sensor_channel, reading.quality
        )
        accepted_by_family["conductivity"] += 1
        accepted += 1

    for reading_payload in payload.chlorophyll_a:
        reading = build_chlorophyll_a_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_chlorophyll_a(reading)
        chlorophyll_a_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_chlorophyll_a_ug_l.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.chlorophyll_a_ug_l)
        record_quality_metric(
            buoy_id, "chlorophyll_a", reading.sensor_channel, reading.quality
        )
        accepted_by_family["chlorophyll_a"] += 1
        accepted += 1

    for reading_payload in payload.rainfall:
        reading = build_rainfall_snapshot(
            buoy_id, reading_payload.model_dump(), payload.device_id
        )
        repository.add_rainfall(reading)
        rainfall_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_rainfall_mm_h.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.rainfall_mm_h)
        record_quality_metric(buoy_id, "rainfall", reading.sensor_channel, reading.quality)
        accepted_by_family["rainfall"] += 1
        accepted += 1

    for reading_payload in payload.humidity:
        reading_data = with_device_provenance(
            reading_payload.model_dump(), payload.device_id
        )
        reading = HumidityReading(buoy_id=buoy_id, **reading_data)
        repository.add_humidity(reading)
        humidity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_humidity_percent.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.humidity_percent)
        record_quality_metric(buoy_id, "humidity", reading.sensor_channel, reading.quality)
        accepted_by_family["humidity"] += 1
        accepted += 1

    for reading_payload in payload.air_temperature:
        reading_data = with_device_provenance(
            reading_payload.model_dump(), payload.device_id
        )
        reading = AirTemperatureReading(buoy_id=buoy_id, **reading_data)
        repository.add_air_temperature(reading)
        air_temperature_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_air_temperature_celsius.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.air_temperature_celsius)
        record_quality_metric(buoy_id, "air_temperature", reading.sensor_channel, reading.quality)
        accepted_by_family["air_temperature"] += 1
        accepted += 1

    for reading_payload in payload.atmospheric_pressure:
        reading_data = with_device_provenance(
            reading_payload.model_dump(), payload.device_id
        )
        reading = AtmosphericPressureReading(buoy_id=buoy_id, **reading_data)
        repository.add_atmospheric_pressure(reading)
        atmospheric_pressure_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_atmospheric_pressure_kpa.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.atmospheric_pressure_kpa)
        record_quality_metric(buoy_id, "atmospheric_pressure", reading.sensor_channel, reading.quality)
        accepted_by_family["atmospheric_pressure"] += 1
        accepted += 1

    for reading_payload in payload.acoustic_altimeter:
        reading_data = with_device_provenance(
            reading_payload.model_dump(), payload.device_id
        )
        reading = AcousticAltimeterReading(buoy_id=buoy_id, **reading_data)
        repository.add_acoustic_altimeter(reading)
        acoustic_altimeter_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_acoustic_altimeter_depth_meters.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.depth_meters)
        record_quality_metric(buoy_id, "acoustic_altimeter", reading.sensor_channel, reading.quality)
        accepted_by_family["acoustic_altimeter"] += 1
        accepted += 1

    for reading_payload in payload.underwater_acoustic:
        reading_data = with_device_provenance(
            reading_payload.model_dump(), payload.device_id
        )
        reading = UnderwaterAcousticReading(buoy_id=buoy_id, **reading_data)
        repository.add_underwater_acoustic(reading)
        underwater_acoustic_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_underwater_acoustic_echo_intensity_db.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.echo_intensity_db)
        record_quality_metric(buoy_id, "underwater_acoustic", reading.sensor_channel, reading.quality)
        accepted_by_family["underwater_acoustic"] += 1
        accepted += 1

    for battery_payload in payload.battery:
        battery = BatteryReading(buoy_id=buoy_id, **battery_payload.model_dump())
        repository.add_battery(battery)
        battery_percent.labels(buoy_id=buoy_id).set(battery.battery_percent)
        battery_device_percent.labels(
            buoy_id=buoy_id, device_id=battery.device_id
        ).set(battery.battery_percent)
        accepted_by_family["battery"] += 1
        accepted += 1

    return TelemetryIngestResponse(
        buoy_id=buoy_id,
        accepted_readings=accepted,
        accepted_by_family=accepted_by_family,
    )
