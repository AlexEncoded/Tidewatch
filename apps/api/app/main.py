from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import time

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db
from .models import (
    Buoy,
    BuoyLocationReading,
    BatteryReading,
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
    ImuReading,
    ImuReadingCreate,
    PressureReading,
    PressureReadingCreate,
    SalinityReading,
    SalinityReadingCreate,
    TemperatureReading,
    TemperatureReadingCreate,
    TelemetryBatchCreate,
    TelemetryIngestResponse,
)
from .repository import BuoyRepository
from .telemetry import configure_telemetry
from .domain.devices import DeviceOwnershipError, validate_device_ownership
from .application.wave_analysis import configured_wave_imu_factor
from .application.device_heartbeat import record_device_heartbeat
from .routers.devices import router as devices_router
from .routers.buoys import router as buoys_router
from .routers.telemetry import router as telemetry_router
from .routers.ingestion import router as ingestion_router
from .routers.analytics import router as analytics_router
from .routers.battery import router as battery_router
from .routers.quality import router as quality_router
from .routers.alerts import router as alerts_router
from .routers.sensors import router as sensors_router
from .routers.maintenance import router as maintenance_router
from .routers.system import router as system_router
from .application.movement_analysis import analyze_movement_for_buoy
from .metrics import (
    battery_percent,
    battery_device_percent,
    buoy_movement_speed_mps,
    buoy_last_seen_timestamp_seconds,
    device_last_seen_timestamp_seconds,
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
    salinity_readings_total,
    temperature_readings_total,
)


logger = logging.getLogger("tidewatch.api")


def record_quality_metric(
    buoy_id: str, sensor_family: str, sensor_channel: str, quality: str
) -> None:
    reading_quality_total.labels(
        buoy_id=buoy_id,
        sensor_family=sensor_family,
        sensor_channel=sensor_channel,
        quality=quality,
    ).inc()


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
app.include_router(devices_router)
app.include_router(buoys_router)
app.include_router(telemetry_router)
app.include_router(ingestion_router)
app.include_router(analytics_router)
app.include_router(battery_router)
app.include_router(quality_router)
app.include_router(alerts_router)
app.include_router(sensors_router)
app.include_router(maintenance_router)
app.include_router(system_router)


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
