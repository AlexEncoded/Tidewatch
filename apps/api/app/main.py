from contextlib import asynccontextmanager
from csv import DictWriter
from datetime import datetime, timezone
from io import StringIO
import logging
from math import sqrt
import os
import time
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .analytics import (
    analyze_battery_health,
    analyze_battery,
    analyze_movement,
    analyze_wave,
    analyze_pressure,
    analyze_temperatures,
)
from .models import (
    Buoy,
    BuoyCreate,
    BuoyHealth,
    BuoyLocationUpdate,
    BuoyLocationReading,
    BuoyStatusUpdate,
    BuoySummary,
    BatteryReading,
    BatteryReadingCreate,
    BatteryHealth,
    AmbientLightReading,
    AmbientLightReadingCreate,
    WindReading,
    WindReadingCreate,
    MarineCurrentReading,
    MarineCurrentReadingCreate,
    TurbidityReading,
    TurbidityReadingCreate,
    DissolvedOxygenReading,
    DissolvedOxygenReadingCreate,
    PHReading,
    PHReadingCreate,
    ConductivityReading,
    ConductivityReadingCreate,
    ChlorophyllAReading,
    ChlorophyllAReadingCreate,
    RainfallReading,
    RainfallReadingCreate,
    HumidityReading,
    HumidityReadingCreate,
    AirTemperatureReading,
    AirTemperatureReadingCreate,
    AtmosphericPressureReading,
    AtmosphericPressureReadingCreate,
    AcousticAltimeterReading,
    AcousticAltimeterReadingCreate,
    UnderwaterAcousticReading,
    UnderwaterAcousticReadingCreate,
    BatteryAnalysis,
    MaintenanceIssue,
    MaintenanceNotificationResult,
    MovementAnalysis,
    WaveAnalysis,
    ImuReading,
    ImuReadingCreate,
    PressureReading,
    PressureReadingCreate,
    PressureAnalysis,
    SalinityReading,
    SalinityReadingCreate,
    SensorHealth,
    SensorHealthCheck,
    QualitySummary,
    TemperatureReading,
    TemperatureReadingCreate,
    TemperatureAnalysis,
    TemperatureAlert,
    StoredTemperatureAlert,
    TelemetryBatchCreate,
    TelemetryIngestResponse,
)
from .repository import BuoyRepository
from .telemetry import configure_telemetry
from .domain.wave import DEFAULT_IMU_WAVE_HEIGHT_FACTOR
from .domain.sensor_health import decide_channel
from .application.wave_analysis import analyze_wave_for_buoy
from .application.movement_analysis import analyze_movement_for_buoy
from .application.pressure_analysis import analyze_pressure_for_buoy
from .application.battery_analysis import analyze_battery_for_buoy
from .application.temperature_analysis import analyze_temperature_for_buoy
from .application.battery_health import analyze_battery_health_for_buoy
from .metrics import (
    battery_percent,
    battery_delta_percent,
    battery_device_percent,
    buoy_movement_speed_mps,
    buoy_last_seen_timestamp_seconds,
    current_pressure_kpa,
    current_salinity_psu,
    current_temperature_celsius,
    current_imu_acceleration_mps2,
    current_imu_angular_velocity_dps,
    current_ambient_light_lux,
    current_wind_speed_mps,
    current_wind_direction_degrees,
    current_marine_current_speed_mps,
    current_marine_current_direction_degrees,
    current_turbidity_ntu,
    current_dissolved_oxygen_mg_l,
    current_ph,
    current_conductivity_us_cm,
    current_chlorophyll_a_ug_l,
    current_rainfall_mm_h,
    current_humidity_percent,
    current_air_temperature_celsius,
    current_atmospheric_pressure_kpa,
    acoustic_altimeter_readings_total,
    current_acoustic_altimeter_depth_meters,
    underwater_acoustic_readings_total,
    current_underwater_acoustic_echo_intensity_db,
    current_gnss_altitude_meters,
    current_gnss_speed_mps,
    current_gnss_hdop,
    current_gnss_satellites,
    current_estimated_wave_height_m,
    http_request_duration_seconds,
    http_requests_total,
    imu_readings_total,
    ambient_light_readings_total,
    wind_readings_total,
    marine_current_readings_total,
    turbidity_readings_total,
    dissolved_oxygen_readings_total,
    ph_readings_total,
    conductivity_readings_total,
    chlorophyll_a_readings_total,
    rainfall_readings_total,
    humidity_readings_total,
    air_temperature_readings_total,
    atmospheric_pressure_readings_total,
    pressure_readings_total,
    reading_quality_total,
    redundant_device_missing,
    salinity_readings_total,
    sensor_channel_missing,
    sensor_degraded,
    sensor_health_decision,
    temperature_readings_total,
)


logger = logging.getLogger("tidewatch.api")


def configured_wave_imu_factor() -> float:
    """Return the bounded experimental IMU calibration factor from the environment."""
    try:
        value = float(os.getenv("WAVE_IMU_WAVE_HEIGHT_FACTOR", str(DEFAULT_IMU_WAVE_HEIGHT_FACTOR)))
    except ValueError:
        return DEFAULT_IMU_WAVE_HEIGHT_FACTOR
    return max(0.0, min(10.0, value))


def record_quality_metric(
    buoy_id: str, sensor_family: str, sensor_channel: str, quality: str
) -> None:
    reading_quality_total.labels(
        buoy_id=buoy_id,
        sensor_family=sensor_family,
        sensor_channel=sensor_channel,
        quality=quality,
    ).inc()


def latest_usable_reading(
    readings: list, max_age_seconds: float | None = None, now: datetime | None = None
) -> list:
    reference_time = now or datetime.now(timezone.utc)
    for reading in readings:
        if reading.quality == "invalid":
            continue
        if max_age_seconds is not None:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=timezone.utc)
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        return [reading]
    return []


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Tidewatch API",
    description="API for monitoring autonomous ocean buoys.",
    version="0.2.0",
    lifespan=lifespan,
)
app.state.otel_enabled = configure_telemetry(app)


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    http_requests_total.labels(
        method=request.method, status_code=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(method=request.method).observe(duration_ms / 1000)
    logger.info(
        "http_request method=%s path=%s status_code=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/buoys", response_model=Buoy, status_code=status.HTTP_201_CREATED, tags=["buoys"])
def create_buoy(payload: BuoyCreate, db: Session = Depends(get_db)) -> Buoy:
    buoy = Buoy(
        id=f"TW-{uuid4().hex[:8].upper()}",
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        created_at=datetime.now(timezone.utc),
    )
    return BuoyRepository(db).create_buoy(buoy)


@app.post(
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

    if payload.location is not None:
        location = BuoyLocationReading(buoy_id=buoy_id, **payload.location.model_dump())
        repository.add_location(location)
        if location.altitude_meters is not None:
            current_gnss_altitude_meters.labels(buoy_id=buoy_id).set(location.altitude_meters)
        if location.speed_mps is not None:
            current_gnss_speed_mps.labels(buoy_id=buoy_id).set(location.speed_mps)
        if location.hdop is not None:
            current_gnss_hdop.labels(buoy_id=buoy_id).set(location.hdop)
        if location.satellites is not None:
            current_gnss_satellites.labels(buoy_id=buoy_id).set(location.satellites)
        movement = analyze_movement(buoy_id, repository.list_locations(buoy_id, 50))
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(
                movement.average_speed_mps
            )

    accepted = 0
    accepted_by_family = {
        "temperature": 0,
        "pressure": 0,
        "salinity": 0,
        "imu": 0,
        "ambient_light": 0,
        "wind": 0,
        "marine_current": 0,
        "turbidity": 0,
        "dissolved_oxygen": 0,
        "ph": 0,
        "conductivity": 0,
        "chlorophyll_a": 0,
        "rainfall": 0,
        "humidity": 0,
        "air_temperature": 0,
        "atmospheric_pressure": 0,
        "acoustic_altimeter": 0,
        "battery": 0,
    }
    for reading_payload in payload.temperatures:
        reading = TemperatureReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = PressureReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = SalinityReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = ImuReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = AmbientLightReading(
            buoy_id=buoy_id, **reading_payload.model_dump()
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
        reading = WindReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = MarineCurrentReading(
            buoy_id=buoy_id, **reading_payload.model_dump()
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
        reading = TurbidityReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = DissolvedOxygenReading(
            buoy_id=buoy_id, **reading_payload.model_dump()
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
        reading = PHReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = ConductivityReading(
            buoy_id=buoy_id, **reading_payload.model_dump()
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
        reading = ChlorophyllAReading(
            buoy_id=buoy_id, **reading_payload.model_dump()
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
        reading = RainfallReading(buoy_id=buoy_id, **reading_payload.model_dump())
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
        reading = HumidityReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_humidity(reading)
        humidity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_humidity_percent.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.humidity_percent)
        record_quality_metric(buoy_id, "humidity", reading.sensor_channel, reading.quality)
        accepted_by_family["humidity"] += 1
        accepted += 1

    for reading_payload in payload.air_temperature:
        reading = AirTemperatureReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_air_temperature(reading)
        air_temperature_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_air_temperature_celsius.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.air_temperature_celsius)
        record_quality_metric(buoy_id, "air_temperature", reading.sensor_channel, reading.quality)
        accepted_by_family["air_temperature"] += 1
        accepted += 1

    for reading_payload in payload.atmospheric_pressure:
        reading = AtmosphericPressureReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_atmospheric_pressure(reading)
        atmospheric_pressure_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_atmospheric_pressure_kpa.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.atmospheric_pressure_kpa)
        record_quality_metric(buoy_id, "atmospheric_pressure", reading.sensor_channel, reading.quality)
        accepted_by_family["atmospheric_pressure"] += 1
        accepted += 1

    for reading_payload in payload.acoustic_altimeter:
        reading = AcousticAltimeterReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_acoustic_altimeter(reading)
        acoustic_altimeter_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_acoustic_altimeter_depth_meters.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.depth_meters)
        record_quality_metric(buoy_id, "acoustic_altimeter", reading.sensor_channel, reading.quality)
        accepted_by_family["acoustic_altimeter"] += 1
        accepted += 1

    for reading_payload in payload.underwater_acoustic:
        reading = UnderwaterAcousticReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_underwater_acoustic(reading)
        underwater_acoustic_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        current_underwater_acoustic_echo_intensity_db.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.echo_intensity_db)
        record_quality_metric(buoy_id, "underwater_acoustic", reading.sensor_channel, reading.quality)
        accepted_by_family["underwater_acoustic"] = accepted_by_family.get("underwater_acoustic", 0) + 1
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


@app.get("/api/v1/buoys", response_model=list[BuoySummary], tags=["buoys"])
def list_buoys(db: Session = Depends(get_db)) -> list[BuoySummary]:
    repository = BuoyRepository(db)
    return [
        BuoySummary(
            buoy=buoy,
            latest_temperature=repository.latest_temperature(buoy.id),
            latest_temperature_a=repository.latest_temperature(buoy.id, "A"),
            latest_temperature_b=repository.latest_temperature(buoy.id, "B"),
            latest_pressure=repository.latest_pressure(buoy.id),
            latest_pressure_a=repository.latest_pressure(buoy.id, "A"),
            latest_pressure_b=repository.latest_pressure(buoy.id, "B"),
            latest_salinity=repository.latest_salinity(buoy.id),
            latest_salinity_a=repository.latest_salinity(buoy.id, "A"),
            latest_salinity_b=repository.latest_salinity(buoy.id, "B"),
            latest_imu=repository.latest_imu(buoy.id),
            latest_imu_a=repository.latest_imu(buoy.id, "A"),
            latest_imu_b=repository.latest_imu(buoy.id, "B"),
            latest_ambient_light=repository.latest_ambient_light(buoy.id),
            latest_ambient_light_a=repository.latest_ambient_light(buoy.id, "A"),
            latest_ambient_light_b=repository.latest_ambient_light(buoy.id, "B"),
            latest_wind=repository.latest_wind(buoy.id),
            latest_wind_a=repository.latest_wind(buoy.id, "A"),
            latest_wind_b=repository.latest_wind(buoy.id, "B"),
            latest_marine_current=repository.latest_marine_current(buoy.id),
            latest_marine_current_a=repository.latest_marine_current(buoy.id, "A"),
            latest_marine_current_b=repository.latest_marine_current(buoy.id, "B"),
            latest_turbidity=repository.latest_turbidity(buoy.id),
            latest_turbidity_a=repository.latest_turbidity(buoy.id, "A"),
            latest_turbidity_b=repository.latest_turbidity(buoy.id, "B"),
            latest_dissolved_oxygen=repository.latest_dissolved_oxygen(buoy.id),
            latest_dissolved_oxygen_a=repository.latest_dissolved_oxygen(buoy.id, "A"),
            latest_dissolved_oxygen_b=repository.latest_dissolved_oxygen(buoy.id, "B"),
            latest_ph=repository.latest_ph(buoy.id),
            latest_ph_a=repository.latest_ph(buoy.id, "A"),
            latest_ph_b=repository.latest_ph(buoy.id, "B"),
            latest_conductivity=repository.latest_conductivity(buoy.id),
            latest_conductivity_a=repository.latest_conductivity(buoy.id, "A"),
            latest_conductivity_b=repository.latest_conductivity(buoy.id, "B"),
            latest_chlorophyll_a=repository.latest_chlorophyll_a(buoy.id),
            latest_chlorophyll_a_a=repository.latest_chlorophyll_a(buoy.id, "A"),
            latest_chlorophyll_a_b=repository.latest_chlorophyll_a(buoy.id, "B"),
            latest_rainfall=repository.latest_rainfall(buoy.id),
            latest_rainfall_a=repository.latest_rainfall(buoy.id, "A"),
            latest_rainfall_b=repository.latest_rainfall(buoy.id, "B"),
            latest_humidity=repository.latest_humidity(buoy.id),
            latest_humidity_a=repository.latest_humidity(buoy.id, "A"),
            latest_humidity_b=repository.latest_humidity(buoy.id, "B"),
            latest_air_temperature=repository.latest_air_temperature(buoy.id),
            latest_air_temperature_a=repository.latest_air_temperature(buoy.id, "A"),
            latest_air_temperature_b=repository.latest_air_temperature(buoy.id, "B"),
            latest_atmospheric_pressure=repository.latest_atmospheric_pressure(buoy.id),
            latest_atmospheric_pressure_a=repository.latest_atmospheric_pressure(buoy.id, "A"),
            latest_atmospheric_pressure_b=repository.latest_atmospheric_pressure(buoy.id, "B"),
            latest_battery=repository.latest_battery(buoy.id),
            latest_battery_a=repository.latest_battery(buoy.id, "A"),
            latest_battery_b=repository.latest_battery(buoy.id, "B"),
        )
        for buoy in repository.list_buoys()
    ]


@app.get("/api/v1/buoys/stale", response_model=list[BuoyHealth], tags=["buoys"])
def stale_buoys(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> list[BuoyHealth]:
    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    stale: list[BuoyHealth] = []

    for buoy in BuoyRepository(db).list_buoys():
        if buoy.status != "active" or buoy.last_seen_at is None:
            continue
        last_seen = buoy.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age_seconds = (now - last_seen).total_seconds()
        if age_seconds > max_age_seconds:
            stale.append(
                BuoyHealth(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    status=buoy.status,
                    last_seen_at=last_seen,
                    age_seconds=round(age_seconds, 2),
                    is_stale=True,
                )
            )

    return stale


@app.patch("/api/v1/buoys/{buoy_id}/status", response_model=Buoy, tags=["buoys"])
def update_buoy_status(
    buoy_id: str,
    payload: BuoyStatusUpdate,
    db: Session = Depends(get_db),
) -> Buoy:
    buoy = BuoyRepository(db).update_status(buoy_id, payload)
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return buoy


@app.patch("/api/v1/buoys/{buoy_id}/location", response_model=Buoy, tags=["buoys"])
def update_buoy_location(
    buoy_id: str,
    payload: BuoyLocationUpdate,
    db: Session = Depends(get_db),
) -> Buoy:
    buoy = BuoyRepository(db).update_location(buoy_id, payload)
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    movement = analyze_movement(buoy_id, BuoyRepository(db).list_locations(buoy_id, 50))
    if movement.average_speed_mps is not None:
        buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(movement.average_speed_mps)
    return buoy


@app.get(
    "/api/v1/buoys/{buoy_id}/locations",
    response_model=list[BuoyLocationReading],
    tags=["buoys"],
)
def list_buoy_locations(
    buoy_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[BuoyLocationReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )
    return repository.list_locations(buoy_id, limit, since, until)


@app.get(
    "/api/v1/buoys/{buoy_id}/locations/export",
    response_class=Response,
    tags=["buoys"],
)
def export_buoy_locations(
    buoy_id: str,
    limit: int = Query(default=500, ge=1, le=5000),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> Response:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )

    output = StringIO()
    writer = DictWriter(
        output,
        fieldnames=["buoy_id", "latitude", "longitude", "measured_at"],
    )
    writer.writeheader()
    for location in repository.list_locations(buoy_id, limit, since, until):
        writer.writerow(
            {
                "buoy_id": location.buoy_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "measured_at": location.measured_at.isoformat(),
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{buoy_id}-locations.csv"'},
    )


@app.get(
    "/api/v1/locations/export",
    response_class=Response,
    tags=["telemetry"],
)
def export_fleet_locations(
    limit: int = Query(default=5000, ge=1, le=50000),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> Response:
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )

    output = StringIO()
    writer = DictWriter(
        output,
        fieldnames=["buoy_id", "latitude", "longitude", "measured_at"],
    )
    writer.writeheader()
    for location in BuoyRepository(db).list_all_locations(limit, since, until):
        writer.writerow(
            {
                "buoy_id": location.buoy_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "measured_at": location.measured_at.isoformat(),
            }
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="tidewatch-locations.csv"'},
    )


@app.get(
    "/api/v1/buoys/{buoy_id}/movement-analysis",
    response_model=MovementAnalysis,
    tags=["buoys"],
)
def buoy_movement_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    db: Session = Depends(get_db),
) -> MovementAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return analyze_movement_for_buoy(repository, buoy_id, window)


@app.get(
    "/api/v1/buoys/{buoy_id}/wave-analysis",
    response_model=WaveAnalysis,
    tags=["analytics"],
)
def buoy_wave_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    db: Session = Depends(get_db),
) -> WaveAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_wave_for_buoy(
        repository,
        buoy_id,
        window,
        configured_wave_imu_factor(),
    )
    if result.estimated_wave_height_m is not None:
        current_estimated_wave_height_m.labels(buoy_id=buoy_id).set(
            result.estimated_wave_height_m
        )
    return result


@app.post(
    "/api/v1/buoys/{buoy_id}/temperatures",
    response_model=TemperatureReading,
    status_code=status.HTTP_201_CREATED,
    tags=["temperature"],
)
def record_temperature(
    buoy_id: str,
    payload: TemperatureReadingCreate,
    db: Session = Depends(get_db),
) -> TemperatureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    reading = TemperatureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_temperature(reading)
    temperature_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_temperature_celsius.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.temperature_celsius)
    record_quality_metric(buoy_id, "temperature", reading.sensor_channel, reading.quality)
    buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(reading.measured_at.timestamp())
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/temperatures",
    response_model=list[TemperatureReading],
    tags=["temperature"],
)
def list_temperatures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[TemperatureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_temperatures(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/pressures",
    response_model=PressureReading,
    status_code=status.HTTP_201_CREATED,
    tags=["pressure"],
)
def record_pressure(
    buoy_id: str,
    payload: PressureReadingCreate,
    db: Session = Depends(get_db),
) -> PressureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = PressureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_pressure(reading)
    pressure_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_pressure_kpa.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.pressure_kpa)
    record_quality_metric(buoy_id, "pressure", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/pressures",
    response_model=list[PressureReading],
    tags=["pressure"],
)
def list_pressures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[PressureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_pressures(buoy_id, limit, sensor_channel)


@app.get(
    "/api/v1/buoys/{buoy_id}/pressure-analysis",
    response_model=PressureAnalysis,
    tags=["pressure"],
)
def pressure_analysis(
    buoy_id: str,
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PressureAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    return analyze_pressure_for_buoy(repository, buoy_id, window)


@app.post(
    "/api/v1/buoys/{buoy_id}/salinity",
    response_model=SalinityReading,
    status_code=status.HTTP_201_CREATED,
    tags=["salinity"],
)
def record_salinity(
    buoy_id: str,
    payload: SalinityReadingCreate,
    db: Session = Depends(get_db),
) -> SalinityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = SalinityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_salinity(reading)
    salinity_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_salinity_psu.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.salinity_psu)
    record_quality_metric(buoy_id, "salinity", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/salinity",
    response_model=list[SalinityReading],
    tags=["salinity"],
)
def list_salinity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[SalinityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_salinity(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/imu",
    response_model=ImuReading,
    status_code=status.HTTP_201_CREATED,
    tags=["imu"],
)
def record_imu(
    buoy_id: str,
    payload: ImuReadingCreate,
    db: Session = Depends(get_db),
) -> ImuReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = ImuReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_imu(reading)
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
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/imu",
    response_model=list[ImuReading],
    tags=["imu"],
)
def list_imu(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[ImuReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_imu(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/ambient-light",
    response_model=AmbientLightReading,
    status_code=status.HTTP_201_CREATED,
    tags=["ambient-light"],
)
def record_ambient_light(
    buoy_id: str,
    payload: AmbientLightReadingCreate,
    db: Session = Depends(get_db),
) -> AmbientLightReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AmbientLightReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_ambient_light(reading)
    ambient_light_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_ambient_light_lux.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.illuminance_lux)
    record_quality_metric(buoy_id, "ambient_light", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/ambient-light",
    response_model=list[AmbientLightReading],
    tags=["ambient-light"],
)
def list_ambient_light(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[AmbientLightReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_ambient_light(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/wind",
    response_model=WindReading,
    status_code=status.HTTP_201_CREATED,
    tags=["wind"],
)
def record_wind(
    buoy_id: str,
    payload: WindReadingCreate,
    db: Session = Depends(get_db),
) -> WindReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = WindReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_wind(reading)
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
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/wind",
    response_model=list[WindReading],
    tags=["wind"],
)
def list_wind(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[WindReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_wind(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/marine-current",
    response_model=MarineCurrentReading,
    status_code=status.HTTP_201_CREATED,
    tags=["marine-current"],
)
def record_marine_current(
    buoy_id: str,
    payload: MarineCurrentReadingCreate,
    db: Session = Depends(get_db),
) -> MarineCurrentReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = MarineCurrentReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_marine_current(reading)
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
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/marine-current",
    response_model=list[MarineCurrentReading],
    tags=["marine-current"],
)
def list_marine_current(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[MarineCurrentReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_marine_current(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/turbidity",
    response_model=TurbidityReading,
    status_code=status.HTTP_201_CREATED,
    tags=["turbidity"],
)
def record_turbidity(
    buoy_id: str,
    payload: TurbidityReadingCreate,
    db: Session = Depends(get_db),
) -> TurbidityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = TurbidityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_turbidity(reading)
    turbidity_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_turbidity_ntu.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.turbidity_ntu)
    record_quality_metric(buoy_id, "turbidity", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/turbidity",
    response_model=list[TurbidityReading],
    tags=["turbidity"],
)
def list_turbidity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[TurbidityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_turbidity(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/dissolved-oxygen",
    response_model=DissolvedOxygenReading,
    status_code=status.HTTP_201_CREATED,
    tags=["dissolved-oxygen"],
)
def record_dissolved_oxygen(
    buoy_id: str,
    payload: DissolvedOxygenReadingCreate,
    db: Session = Depends(get_db),
) -> DissolvedOxygenReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = DissolvedOxygenReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_dissolved_oxygen(reading)
    dissolved_oxygen_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_dissolved_oxygen_mg_l.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.dissolved_oxygen_mg_l)
    record_quality_metric(
        buoy_id, "dissolved_oxygen", reading.sensor_channel, reading.quality
    )
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/dissolved-oxygen",
    response_model=list[DissolvedOxygenReading],
    tags=["dissolved-oxygen"],
)
def list_dissolved_oxygen(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[DissolvedOxygenReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_dissolved_oxygen(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/ph",
    response_model=PHReading,
    status_code=status.HTTP_201_CREATED,
    tags=["ph"],
)
def record_ph(
    buoy_id: str,
    payload: PHReadingCreate,
    db: Session = Depends(get_db),
) -> PHReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = PHReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_ph(reading)
    ph_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_ph.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.ph)
    record_quality_metric(buoy_id, "ph", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/ph",
    response_model=list[PHReading],
    tags=["ph"],
)
def list_ph(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[PHReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_ph(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/conductivity",
    response_model=ConductivityReading,
    status_code=status.HTTP_201_CREATED,
    tags=["conductivity"],
)
def record_conductivity(
    buoy_id: str,
    payload: ConductivityReadingCreate,
    db: Session = Depends(get_db),
) -> ConductivityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = ConductivityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_conductivity(reading)
    conductivity_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_conductivity_us_cm.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.conductivity_us_cm)
    record_quality_metric(
        buoy_id, "conductivity", reading.sensor_channel, reading.quality
    )
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/conductivity",
    response_model=list[ConductivityReading],
    tags=["conductivity"],
)
def list_conductivity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[ConductivityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_conductivity(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/chlorophyll-a",
    response_model=ChlorophyllAReading,
    status_code=status.HTTP_201_CREATED,
    tags=["chlorophyll-a"],
)
def record_chlorophyll_a(
    buoy_id: str,
    payload: ChlorophyllAReadingCreate,
    db: Session = Depends(get_db),
) -> ChlorophyllAReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = ChlorophyllAReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_chlorophyll_a(reading)
    chlorophyll_a_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_chlorophyll_a_ug_l.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.chlorophyll_a_ug_l)
    record_quality_metric(
        buoy_id, "chlorophyll_a", reading.sensor_channel, reading.quality
    )
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/chlorophyll-a",
    response_model=list[ChlorophyllAReading],
    tags=["chlorophyll-a"],
)
def list_chlorophyll_a(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[ChlorophyllAReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_chlorophyll_a(buoy_id, limit, sensor_channel)


@app.post("/api/v1/buoys/{buoy_id}/rainfall", response_model=RainfallReading, status_code=status.HTTP_201_CREATED, tags=["rainfall"])
def record_rainfall(buoy_id: str, payload: RainfallReadingCreate, db: Session = Depends(get_db)) -> RainfallReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = RainfallReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_rainfall(reading)
    rainfall_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_rainfall_mm_h.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.rainfall_mm_h)
    record_quality_metric(buoy_id, "rainfall", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get("/api/v1/buoys/{buoy_id}/rainfall", response_model=list[RainfallReading], tags=["rainfall"])
def list_rainfall(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[RainfallReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_rainfall(buoy_id, limit, sensor_channel)


@app.post("/api/v1/buoys/{buoy_id}/humidity", response_model=HumidityReading, status_code=status.HTTP_201_CREATED, tags=["humidity"])
def record_humidity(buoy_id: str, payload: HumidityReadingCreate, db: Session = Depends(get_db)) -> HumidityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = HumidityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_humidity(reading)
    humidity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_humidity_percent.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.humidity_percent)
    record_quality_metric(buoy_id, "humidity", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get("/api/v1/buoys/{buoy_id}/humidity", response_model=list[HumidityReading], tags=["humidity"])
def list_humidity(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[HumidityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_humidity(buoy_id, limit, sensor_channel)


@app.post("/api/v1/buoys/{buoy_id}/air-temperature", response_model=AirTemperatureReading, status_code=status.HTTP_201_CREATED, tags=["air-temperature"])
def record_air_temperature(buoy_id: str, payload: AirTemperatureReadingCreate, db: Session = Depends(get_db)) -> AirTemperatureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AirTemperatureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_air_temperature(reading)
    air_temperature_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_air_temperature_celsius.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.air_temperature_celsius)
    record_quality_metric(buoy_id, "air_temperature", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get("/api/v1/buoys/{buoy_id}/air-temperature", response_model=list[AirTemperatureReading], tags=["air-temperature"])
def list_air_temperature(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AirTemperatureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_air_temperature(buoy_id, limit, sensor_channel)


@app.post("/api/v1/buoys/{buoy_id}/atmospheric-pressure", response_model=AtmosphericPressureReading, status_code=status.HTTP_201_CREATED, tags=["atmospheric-pressure"])
def record_atmospheric_pressure(buoy_id: str, payload: AtmosphericPressureReadingCreate, db: Session = Depends(get_db)) -> AtmosphericPressureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AtmosphericPressureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_atmospheric_pressure(reading)
    atmospheric_pressure_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_atmospheric_pressure_kpa.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.atmospheric_pressure_kpa)
    record_quality_metric(buoy_id, "atmospheric_pressure", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get("/api/v1/buoys/{buoy_id}/atmospheric-pressure", response_model=list[AtmosphericPressureReading], tags=["atmospheric-pressure"])
def list_atmospheric_pressure(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AtmosphericPressureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_atmospheric_pressure(buoy_id, limit, sensor_channel)


@app.post("/api/v1/buoys/{buoy_id}/acoustic-altimeter", response_model=AcousticAltimeterReading, status_code=status.HTTP_201_CREATED, tags=["acoustic-altimeter"])
def record_acoustic_altimeter(buoy_id: str, payload: AcousticAltimeterReadingCreate, db: Session = Depends(get_db)) -> AcousticAltimeterReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AcousticAltimeterReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_acoustic_altimeter(reading)
    acoustic_altimeter_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_acoustic_altimeter_depth_meters.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.depth_meters)
    record_quality_metric(buoy_id, "acoustic_altimeter", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get("/api/v1/buoys/{buoy_id}/acoustic-altimeter", response_model=list[AcousticAltimeterReading], tags=["acoustic-altimeter"])
def list_acoustic_altimeter(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AcousticAltimeterReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_acoustic_altimeter(buoy_id, limit, sensor_channel)


@app.post("/api/v1/buoys/{buoy_id}/underwater-acoustic", response_model=UnderwaterAcousticReading, status_code=status.HTTP_201_CREATED, tags=["underwater-acoustic"])
def record_underwater_acoustic(buoy_id: str, payload: UnderwaterAcousticReadingCreate, db: Session = Depends(get_db)) -> UnderwaterAcousticReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = UnderwaterAcousticReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_underwater_acoustic(reading)
    underwater_acoustic_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_underwater_acoustic_echo_intensity_db.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.echo_intensity_db)
    record_quality_metric(buoy_id, "underwater_acoustic", reading.sensor_channel, reading.quality)
    return saved_reading


@app.get("/api/v1/buoys/{buoy_id}/underwater-acoustic", response_model=list[UnderwaterAcousticReading], tags=["underwater-acoustic"])
def list_underwater_acoustic(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[UnderwaterAcousticReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_underwater_acoustic(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/battery",
    response_model=BatteryReading,
    status_code=status.HTTP_201_CREATED,
    tags=["battery"],
)
def record_battery(
    buoy_id: str,
    payload: BatteryReadingCreate,
    db: Session = Depends(get_db),
) -> BatteryReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    battery = BatteryReading(buoy_id=buoy_id, **payload.model_dump())
    saved_battery = repository.add_battery(battery)
    battery_percent.labels(buoy_id=buoy_id).set(battery.battery_percent)
    return saved_battery


@app.get(
    "/api/v1/buoys/{buoy_id}/battery",
    response_model=BatteryReading | None,
    tags=["battery"],
)
def latest_battery(
    buoy_id: str,
    device_id: str | None = Query(default=None, pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> BatteryReading | None:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.latest_battery(buoy_id, device_id)


@app.get(
    "/api/v1/buoys/{buoy_id}/battery/history",
    response_model=list[BatteryReading],
    tags=["battery"],
)
def battery_history(
    buoy_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    device_id: str | None = Query(default=None, pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[BatteryReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_batteries(buoy_id, limit, device_id)


@app.get(
    "/api/v1/buoys/{buoy_id}/battery-analysis",
    response_model=BatteryAnalysis,
    tags=["battery"],
)
def battery_analysis(
    buoy_id: str,
    device_id: str = Query(default="A", pattern="^(A|B)$"),
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> BatteryAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return analyze_battery_for_buoy(repository, buoy_id, device_id, window)


@app.get(
    "/api/v1/buoys/{buoy_id}/battery-health",
    response_model=BatteryHealth,
    tags=["battery"],
)
def battery_health(
    buoy_id: str,
    threshold: float = Query(default=10, gt=0, le=100),
    db: Session = Depends(get_db),
) -> BatteryHealth:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_battery_health_for_buoy(repository, buoy_id, threshold)
    for device_id, percentage in (
        ("A", result.device_a_percent),
        ("B", result.device_b_percent),
    ):
        if percentage is not None:
            battery_device_percent.labels(
                buoy_id=buoy_id, device_id=device_id
            ).set(percentage)
    if result.delta_percent is not None:
        battery_delta_percent.labels(buoy_id=buoy_id).set(result.delta_percent)
    return result


@app.get(
    "/api/v1/buoys/{buoy_id}/quality-summary",
    response_model=QualitySummary,
    tags=["quality"],
)
def quality_summary(buoy_id: str, db: Session = Depends(get_db)) -> QualitySummary:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    counts = repository.quality_counts(buoy_id)
    return QualitySummary(
        buoy_id=buoy_id,
        total_readings=sum(counts.values()),
        good_readings=counts["good"],
        suspect_readings=counts["suspect"],
        invalid_readings=counts["invalid"],
    )


@app.get(
    "/api/v1/buoys/{buoy_id}/sensor-health",
    response_model=SensorHealth,
    tags=["sensors"],
)
def sensor_health(
    buoy_id: str,
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> SensorHealth:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    temperature_a = latest_usable_reading(
        repository.list_temperatures(buoy_id, 50, "A"), max_age_seconds, now
    )
    temperature_b = latest_usable_reading(
        repository.list_temperatures(buoy_id, 50, "B"), max_age_seconds, now
    )
    pressure_a = latest_usable_reading(
        repository.list_pressures(buoy_id, 50, "A"), max_age_seconds, now
    )
    pressure_b = latest_usable_reading(
        repository.list_pressures(buoy_id, 50, "B"), max_age_seconds, now
    )
    salinity_a = latest_usable_reading(
        repository.list_salinity(buoy_id, 50, "A"), max_age_seconds, now
    )
    salinity_b = latest_usable_reading(
        repository.list_salinity(buoy_id, 50, "B"), max_age_seconds, now
    )
    imu_a = latest_usable_reading(
        repository.list_imu(buoy_id, 50, "A"), max_age_seconds, now
    )
    imu_b = latest_usable_reading(
        repository.list_imu(buoy_id, 50, "B"), max_age_seconds, now
    )
    ambient_light_a = latest_usable_reading(
        repository.list_ambient_light(buoy_id, 50, "A"), max_age_seconds, now
    )
    ambient_light_b = latest_usable_reading(
        repository.list_ambient_light(buoy_id, 50, "B"), max_age_seconds, now
    )
    wind_a = latest_usable_reading(
        repository.list_wind(buoy_id, 50, "A"), max_age_seconds, now
    )
    wind_b = latest_usable_reading(
        repository.list_wind(buoy_id, 50, "B"), max_age_seconds, now
    )
    marine_current_a = latest_usable_reading(
        repository.list_marine_current(buoy_id, 50, "A"), max_age_seconds, now
    )
    marine_current_b = latest_usable_reading(
        repository.list_marine_current(buoy_id, 50, "B"), max_age_seconds, now
    )
    turbidity_a = latest_usable_reading(
        repository.list_turbidity(buoy_id, 50, "A"), max_age_seconds, now
    )
    turbidity_b = latest_usable_reading(
        repository.list_turbidity(buoy_id, 50, "B"), max_age_seconds, now
    )
    dissolved_oxygen_a = latest_usable_reading(
        repository.list_dissolved_oxygen(buoy_id, 50, "A"), max_age_seconds, now
    )
    dissolved_oxygen_b = latest_usable_reading(
        repository.list_dissolved_oxygen(buoy_id, 50, "B"), max_age_seconds, now
    )
    ph_a = latest_usable_reading(
        repository.list_ph(buoy_id, 50, "A"), max_age_seconds, now
    )
    ph_b = latest_usable_reading(
        repository.list_ph(buoy_id, 50, "B"), max_age_seconds, now
    )
    conductivity_a = latest_usable_reading(
        repository.list_conductivity(buoy_id, 50, "A"), max_age_seconds, now
    )
    conductivity_b = latest_usable_reading(
        repository.list_conductivity(buoy_id, 50, "B"), max_age_seconds, now
    )
    chlorophyll_a = latest_usable_reading(
        repository.list_chlorophyll_a(buoy_id, 50, "A"), max_age_seconds, now
    )
    chlorophyll_b = latest_usable_reading(
        repository.list_chlorophyll_a(buoy_id, 50, "B"), max_age_seconds, now
    )
    rainfall_a = latest_usable_reading(
        repository.list_rainfall(buoy_id, 50, "A"), max_age_seconds, now
    )
    rainfall_b = latest_usable_reading(
        repository.list_rainfall(buoy_id, 50, "B"), max_age_seconds, now
    )
    humidity_a = latest_usable_reading(
        repository.list_humidity(buoy_id, 50, "A"), max_age_seconds, now
    )
    humidity_b = latest_usable_reading(
        repository.list_humidity(buoy_id, 50, "B"), max_age_seconds, now
    )
    air_temperature_a = latest_usable_reading(
        repository.list_air_temperature(buoy_id, 50, "A"), max_age_seconds, now
    )
    air_temperature_b = latest_usable_reading(
        repository.list_air_temperature(buoy_id, 50, "B"), max_age_seconds, now
    )
    atmospheric_pressure_a = latest_usable_reading(
        repository.list_atmospheric_pressure(buoy_id, 50, "A"), max_age_seconds, now
    )
    atmospheric_pressure_b = latest_usable_reading(
        repository.list_atmospheric_pressure(buoy_id, 50, "B"), max_age_seconds, now
    )
    acoustic_altimeter_a = latest_usable_reading(
        repository.list_acoustic_altimeter(buoy_id, 50, "A"), max_age_seconds, now
    )
    acoustic_altimeter_b = latest_usable_reading(
        repository.list_acoustic_altimeter(buoy_id, 50, "B"), max_age_seconds, now
    )
    underwater_acoustic_a = latest_usable_reading(
        repository.list_underwater_acoustic(buoy_id, 50, "A"), max_age_seconds, now
    )
    underwater_acoustic_b = latest_usable_reading(
        repository.list_underwater_acoustic(buoy_id, 50, "B"), max_age_seconds, now
    )

    sensor_readings = {
        "temperature": {"A": temperature_a, "B": temperature_b},
        "pressure": {"A": pressure_a, "B": pressure_b},
        "salinity": {"A": salinity_a, "B": salinity_b},
        "imu": {"A": imu_a, "B": imu_b},
        "ambient_light": {"A": ambient_light_a, "B": ambient_light_b},
        "wind": {"A": wind_a, "B": wind_b},
        "marine_current": {"A": marine_current_a, "B": marine_current_b},
        "turbidity": {"A": turbidity_a, "B": turbidity_b},
        "dissolved_oxygen": {"A": dissolved_oxygen_a, "B": dissolved_oxygen_b},
        "ph": {"A": ph_a, "B": ph_b},
        "conductivity": {"A": conductivity_a, "B": conductivity_b},
        "chlorophyll_a": {"A": chlorophyll_a, "B": chlorophyll_b},
        "rainfall": {"A": rainfall_a, "B": rainfall_b},
        "humidity": {"A": humidity_a, "B": humidity_b},
        "air_temperature": {"A": air_temperature_a, "B": air_temperature_b},
        "atmospheric_pressure": {"A": atmospheric_pressure_a, "B": atmospheric_pressure_b},
        "acoustic_altimeter": {"A": acoustic_altimeter_a, "B": acoustic_altimeter_b},
        "underwater_acoustic": {"A": underwater_acoustic_a, "B": underwater_acoustic_b},
    }
    missing_sensors = [
        f"{sensor}:{channel}"
        for sensor, channels in sensor_readings.items()
        if any(channels.values())
        for channel, reading in channels.items()
        if not reading
    ]

    deltas = {
        "temperature": (
            round(abs(temperature_a[0].temperature_celsius - temperature_b[0].temperature_celsius), 3)
            if temperature_a and temperature_b
            else None
        ),
        "pressure": (
            round(abs(pressure_a[0].pressure_kpa - pressure_b[0].pressure_kpa), 3)
            if pressure_a and pressure_b
            else None
        ),
        "salinity": (
            round(abs(salinity_a[0].salinity_psu - salinity_b[0].salinity_psu), 3)
            if salinity_a and salinity_b
            else None
        ),
        "imu": (
            round(
                sqrt(
                    sum(
                        (
                            getattr(imu_a[0], f"acceleration_{axis}_mps2")
                            - getattr(imu_b[0], f"acceleration_{axis}_mps2")
                        )
                        ** 2
                        for axis in ("x", "y", "z")
                    )
                ),
                3,
            )
            if imu_a and imu_b
            else None
        ),
        "ambient_light": (
            round(
                abs(
                    ambient_light_a[0].illuminance_lux
                    - ambient_light_b[0].illuminance_lux
                ),
                2,
            )
            if ambient_light_a and ambient_light_b
            else None
        ),
        "wind_speed": (
            round(abs(wind_a[0].wind_speed_mps - wind_b[0].wind_speed_mps), 3)
            if wind_a and wind_b
            else None
        ),
        "wind_direction": (
            round(
                min(
                    abs(wind_a[0].wind_direction_degrees - wind_b[0].wind_direction_degrees),
                    360
                    - abs(
                        wind_a[0].wind_direction_degrees
                        - wind_b[0].wind_direction_degrees
                    ),
                ),
                2,
            )
            if wind_a and wind_b
            else None
        ),
        "marine_current_speed": (
            round(
                abs(
                    marine_current_a[0].current_speed_mps
                    - marine_current_b[0].current_speed_mps
                ),
                3,
            )
            if marine_current_a and marine_current_b
            else None
        ),
        "marine_current_direction": (
            round(
                min(
                    abs(
                        marine_current_a[0].current_direction_degrees
                        - marine_current_b[0].current_direction_degrees
                    ),
                    360
                    - abs(
                        marine_current_a[0].current_direction_degrees
                        - marine_current_b[0].current_direction_degrees
                    ),
                ),
                2,
            )
            if marine_current_a and marine_current_b
            else None
        ),
        "turbidity": (
            round(abs(turbidity_a[0].turbidity_ntu - turbidity_b[0].turbidity_ntu), 3)
            if turbidity_a and turbidity_b
            else None
        ),
        "dissolved_oxygen": (
            round(
                abs(
                    dissolved_oxygen_a[0].dissolved_oxygen_mg_l
                    - dissolved_oxygen_b[0].dissolved_oxygen_mg_l
                ),
                3,
            )
            if dissolved_oxygen_a and dissolved_oxygen_b
            else None
        ),
        "ph": (
            round(abs(ph_a[0].ph - ph_b[0].ph), 3)
            if ph_a and ph_b
            else None
        ),
        "conductivity": (
            round(
                abs(
                    conductivity_a[0].conductivity_us_cm
                    - conductivity_b[0].conductivity_us_cm
                ),
                2,
            )
            if conductivity_a and conductivity_b
            else None
        ),
        "chlorophyll_a": (
            round(
                abs(
                    chlorophyll_a[0].chlorophyll_a_ug_l
                    - chlorophyll_b[0].chlorophyll_a_ug_l
                ),
                3,
            )
            if chlorophyll_a and chlorophyll_b
            else None
        ),
        "rainfall": (
            round(abs(rainfall_a[0].rainfall_mm_h - rainfall_b[0].rainfall_mm_h), 2)
            if rainfall_a and rainfall_b
            else None
        ),
        "humidity": (
            round(abs(humidity_a[0].humidity_percent - humidity_b[0].humidity_percent), 2)
            if humidity_a and humidity_b
            else None
        ),
        "air_temperature": (
            round(abs(air_temperature_a[0].air_temperature_celsius - air_temperature_b[0].air_temperature_celsius), 2)
            if air_temperature_a and air_temperature_b
            else None
        ),
        "atmospheric_pressure": (
            round(abs(atmospheric_pressure_a[0].atmospheric_pressure_kpa - atmospheric_pressure_b[0].atmospheric_pressure_kpa), 3)
            if atmospheric_pressure_a and atmospheric_pressure_b
            else None
        ),
        "acoustic_altimeter": (
            round(abs(acoustic_altimeter_a[0].depth_meters - acoustic_altimeter_b[0].depth_meters), 3)
            if acoustic_altimeter_a and acoustic_altimeter_b
            else None
        ),
        "underwater_acoustic": (
            round(abs(underwater_acoustic_a[0].echo_intensity_db - underwater_acoustic_b[0].echo_intensity_db), 2)
            if underwater_acoustic_a and underwater_acoustic_b
            else None
        ),
    }
    available = [value for value in deltas.values() if value is not None]
    thresholds = {
        "temperature": 0.5,
        "pressure": 0.25,
        "salinity": 0.2,
        "imu": 0.5,
        "ambient_light": 5000,
        "wind_speed": 0.5,
        "wind_direction": 15,
        "marine_current_speed": 0.25,
        "marine_current_direction": 15,
        "turbidity": 10,
        "dissolved_oxygen": 1,
        "ph": 0.2,
        "conductivity": 2000,
        "chlorophyll_a": 5,
        "rainfall": 20,
        "humidity": 5,
        "air_temperature": 0.5,
        "atmospheric_pressure": 0.25,
        "acoustic_altimeter": 0.5,
        "underwater_acoustic": 5,
    }
    degraded_sensors = [
        sensor
        for sensor, value in deltas.items()
        if value is not None and value > thresholds[sensor]
    ]
    if "wind_speed" in degraded_sensors or "wind_direction" in degraded_sensors:
        degraded_sensors.append("wind")
    if (
        "marine_current_speed" in degraded_sensors
        or "marine_current_direction" in degraded_sensors
    ):
        degraded_sensors.append("marine_current")
    status_value = "insufficient_data"
    if available:
        status_value = "degraded" if degraded_sensors else "consistent"

    for sensor, channels in sensor_readings.items():
        has_reading = any(channels.values())
        for channel, reading in channels.items():
            sensor_channel_missing.labels(
                buoy_id=buoy_id, sensor=sensor, sensor_channel=channel
            ).set(1 if has_reading and not reading else 0)
        sensor_degraded.labels(buoy_id=buoy_id, sensor=sensor).set(
            1 if sensor in degraded_sensors or any(
                missing.startswith(f"{sensor}:") for missing in missing_sensors
            ) else 0
        )

    status_value = "degraded" if degraded_sensors or missing_sensors else status_value
    decisions = {}
    for sensor, channels in sensor_readings.items():
        decisions[sensor] = decide_channel(
            bool(channels["A"]),
            bool(channels["B"]),
            sensor in degraded_sensors,
        )
        for decision in ("average", "fallback_a", "fallback_b", "invalid"):
            sensor_health_decision.labels(
                buoy_id=buoy_id, sensor=sensor, decision=decision
            ).set(1 if decisions[sensor] == decision else 0)
    return SensorHealth(
        buoy_id=buoy_id,
        status=status_value,
        temperature_delta_celsius=deltas["temperature"],
        pressure_delta_kpa=deltas["pressure"],
        salinity_delta_psu=deltas["salinity"],
        imu_acceleration_delta_mps2=deltas["imu"],
        ambient_light_delta_lux=deltas["ambient_light"],
        wind_speed_delta_mps=deltas["wind_speed"],
        wind_direction_delta_degrees=deltas["wind_direction"],
        marine_current_speed_delta_mps=deltas["marine_current_speed"],
        marine_current_direction_delta_degrees=deltas["marine_current_direction"],
        turbidity_delta_ntu=deltas["turbidity"],
        dissolved_oxygen_delta_mg_l=deltas["dissolved_oxygen"],
        ph_delta=deltas["ph"],
        conductivity_delta_us_cm=deltas["conductivity"],
        chlorophyll_a_delta_ug_l=deltas["chlorophyll_a"],
        rainfall_delta_mm_h=deltas["rainfall"],
        humidity_delta_percent=deltas["humidity"],
        air_temperature_delta_celsius=deltas["air_temperature"],
        atmospheric_pressure_delta_kpa=deltas["atmospheric_pressure"],
        acoustic_altimeter_delta_meters=deltas["acoustic_altimeter"],
        underwater_acoustic_delta_db=deltas["underwater_acoustic"],
        degraded_sensors=degraded_sensors,
        missing_sensors=missing_sensors,
        decisions=decisions,
        checked_at=now,
    )


@app.post(
    "/api/v1/buoys/{buoy_id}/sensor-health/check",
    response_model=SensorHealthCheck,
    status_code=status.HTTP_201_CREATED,
    tags=["sensors"],
)
def record_sensor_health_check(
    buoy_id: str,
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> SensorHealthCheck:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    health = sensor_health(buoy_id, max_age_minutes=max_age_minutes, db=db)
    return repository.add_sensor_health_check(health)


@app.get(
    "/api/v1/buoys/{buoy_id}/sensor-health/history",
    response_model=list[SensorHealthCheck],
    tags=["sensors"],
)
def sensor_health_history(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[SensorHealthCheck]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_sensor_health_checks(buoy_id, limit)


@app.get(
    "/api/v1/maintenance/issues",
    response_model=list[MaintenanceIssue],
    tags=["maintenance"],
)
def maintenance_issues(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    db: Session = Depends(get_db),
) -> list[MaintenanceIssue]:
    repository = BuoyRepository(db)
    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    issues: list[MaintenanceIssue] = []

    for buoy in repository.list_buoys():
        if buoy.status == "active" and buoy.last_seen_at is not None:
            last_seen = buoy.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if (now - last_seen).total_seconds() > max_age_seconds:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="silent_buoy",
                        severity="warning",
                        message=f"No telemetry received for more than {max_age_minutes:g} minutes",
                    )
                )

        health = sensor_health(buoy.id, max_age_minutes=max_age_minutes, db=db)
        if health.status == "degraded":
            if health.degraded_sensors:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="degraded_sensor",
                        severity="warning",
                        message=f"Degraded sensors: {', '.join(health.degraded_sensors)}",
                    )
                )
            if health.missing_sensors:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="missing_sensor_channel",
                        severity="warning",
                        message=(
                            "No recent telemetry received from sensor channels: "
                            f"{', '.join(health.missing_sensors)}"
                        ),
                    )
                )

        latest_readings = {
            "temperature": repository.list_temperatures(buoy.id, 1),
            "pressure": repository.list_pressures(buoy.id, 1),
            "salinity": repository.list_salinity(buoy.id, 1),
        }
        invalid_sensors = [
            sensor
            for sensor, readings in latest_readings.items()
            if readings and readings[0].quality == "invalid"
        ]
        if invalid_sensors:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="invalid_reading",
                    severity="warning",
                    message=f"Invalid latest readings: {', '.join(invalid_sensors)}",
                )
            )

        suspect_sensors = [
            sensor
            for sensor, readings in latest_readings.items()
            if readings and readings[0].quality == "suspect"
        ]
        if suspect_sensors:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="suspect_reading",
                    severity="warning",
                    message=f"Suspect latest readings: {', '.join(suspect_sensors)}",
                )
            )

        for device_id in ("A", "B"):
            battery = repository.latest_battery(buoy.id, device_id)
            if battery is not None and battery.battery_percent < 20:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="low_battery",
                        severity="critical" if battery.battery_percent < 10 else "warning",
                        message=(
                            f"Battery level for device {device_id} is "
                            f"{battery.battery_percent:.1f}%"
                        ),
                    )
                )

        battery_readings = {}
        for device_id in ("A", "B"):
            reading = repository.latest_battery(buoy.id, device_id)
            battery_readings[device_id] = BatteryReading.model_validate(reading) if reading else None
        battery_health_result = analyze_battery_health(buoy.id, battery_readings, 10)
        for device_id, reading in battery_readings.items():
            if reading is not None:
                battery_device_percent.labels(
                    buoy_id=buoy.id, device_id=device_id
                ).set(reading.battery_percent)
        if battery_health_result.delta_percent is not None:
            battery_delta_percent.labels(buoy_id=buoy.id).set(
                battery_health_result.delta_percent
            )
        available_battery_devices = [
            device_id for device_id, reading in battery_readings.items() if reading is not None
        ]
        for device_id in ("A", "B"):
            redundant_device_missing.labels(
                buoy_id=buoy.id, device_id=device_id
            ).set(0 if device_id in available_battery_devices else 1)
        if len(available_battery_devices) == 1:
            missing_device = "B" if available_battery_devices[0] == "A" else "A"
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="missing_redundant_device",
                    severity="warning",
                    message=(
                        f"No battery telemetry received from redundant device {missing_device}"
                    ),
                )
            )
        if battery_health_result.status == "degraded":
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="degraded_battery",
                    severity="warning",
                    message=(
                        f"Battery units diverge by {battery_health_result.delta_percent:.1f}% "
                        f"(unit {', '.join(battery_health_result.degraded_devices)} suspected)"
                    ),
                )
            )

        movement = analyze_movement_for_buoy(repository, buoy.id, 50)
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy.id).set(movement.average_speed_mps)
        if (
            movement.average_speed_mps is not None
            and movement.average_speed_mps > drift_speed_mps
        ):
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="drift_detected",
                    severity="warning",
                    message=(
                        f"Average movement speed is {movement.average_speed_mps:.3f} m/s, "
                        f"above the configured limit of {drift_speed_mps:g} m/s"
                    ),
                )
            )

    return issues


@app.post(
    "/api/v1/maintenance/notifications",
    response_model=MaintenanceNotificationResult,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["maintenance"],
)
def notify_maintenance(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    db: Session = Depends(get_db),
) -> MaintenanceNotificationResult:
    webhook_url = os.getenv("MAINTENANCE_WEBHOOK_URL")
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MAINTENANCE_WEBHOOK_URL is not configured",
        )

    issues = maintenance_issues(
        max_age_minutes=max_age_minutes, drift_speed_mps=drift_speed_mps, db=db
    )
    payload = {
        "source": "tidewatch",
        "issues": [issue.model_dump(mode="json") for issue in issues],
    }
    try:
        response = httpx.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Maintenance webhook delivery failed",
        ) from exc

    return MaintenanceNotificationResult(status="sent", issue_count=len(issues))


@app.get(
    "/api/v1/buoys/{buoy_id}/temperature-analysis",
    response_model=TemperatureAnalysis,
    tags=["temperature"],
)
def temperature_analysis(
    buoy_id: str,
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> TemperatureAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    return analyze_temperature_for_buoy(repository, buoy_id, window, threshold)


@app.get(
    "/api/v1/alerts/temperature",
    response_model=list[TemperatureAlert],
    tags=["alerts"],
)
def temperature_alerts(
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TemperatureAlert]:
    repository = BuoyRepository(db)
    alerts: list[TemperatureAlert] = []

    for buoy in repository.list_buoys():
        readings = [
            TemperatureReading.model_validate(reading)
            for reading in repository.list_temperatures(buoy.id, window)
            if reading.quality != "invalid"
        ]
        analysis = analyze_temperatures(buoy.id, readings, threshold)
        if analysis.is_anomaly and analysis.latest_temperature is not None:
            alerts.append(
                TemperatureAlert(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    severity="warning",
                    temperature_celsius=analysis.latest_temperature,
                    average_temperature=analysis.average_temperature or 0,
                    created_at=readings[0].measured_at,
                    message=analysis.anomaly_reason or "Temperature anomaly detected",
                )
            )

    return alerts


def stored_alert_response(alert) -> StoredTemperatureAlert:
    return StoredTemperatureAlert(
        id=alert.id,
        buoy_id=alert.buoy_id,
        buoy_name=alert.buoy.name,
        severity=alert.severity,
        temperature_celsius=alert.temperature_celsius,
        average_temperature=alert.average_temperature,
        created_at=alert.created_at,
        message=alert.message,
        status=alert.status,
        resolved_at=alert.resolved_at,
    )


@app.post(
    "/api/v1/alerts/temperature/evaluate",
    response_model=list[StoredTemperatureAlert],
    tags=["alerts"],
)
def evaluate_temperature_alerts(
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[StoredTemperatureAlert]:
    repository = BuoyRepository(db)
    stored_alerts = []

    for buoy in repository.list_buoys():
        readings = [
            TemperatureReading.model_validate(reading)
            for reading in repository.list_temperatures(buoy.id, window)
            if reading.quality != "invalid"
        ]
        analysis = analyze_temperatures(buoy.id, readings, threshold)
        if not analysis.is_anomaly or not readings:
            continue

        current_reading = readings[0]
        existing = repository.find_alert(buoy.id, current_reading.measured_at)
        if existing is None:
            alert = TemperatureAlert(
                buoy_id=buoy.id,
                buoy_name=buoy.name,
                severity="warning",
                temperature_celsius=analysis.latest_temperature or 0,
                average_temperature=analysis.average_temperature or 0,
                created_at=current_reading.measured_at,
                message=analysis.anomaly_reason or "Temperature anomaly detected",
            )
            existing = repository.create_alert(alert, current_reading.measured_at)
        stored_alerts.append(stored_alert_response(existing))

    return stored_alerts


@app.get(
    "/api/v1/alerts/temperature/stored",
    response_model=list[StoredTemperatureAlert],
    tags=["alerts"],
)
def stored_temperature_alerts(
    status_filter: str = Query(default="open", alias="status", pattern="^(open|resolved)$"),
    db: Session = Depends(get_db),
) -> list[StoredTemperatureAlert]:
    return [stored_alert_response(alert) for alert in BuoyRepository(db).list_alerts(status_filter)]


@app.post(
    "/api/v1/alerts/temperature/{alert_id}/resolve",
    response_model=StoredTemperatureAlert,
    tags=["alerts"],
)
def resolve_temperature_alert(alert_id: int, db: Session = Depends(get_db)) -> StoredTemperatureAlert:
    alert = BuoyRepository(db).resolve_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return stored_alert_response(alert)
