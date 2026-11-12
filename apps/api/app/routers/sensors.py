"""Specialized sensor telemetry endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..adapter_dependencies import get_temperature_telemetry_gateway
from ..adapter_dependencies import get_pressure_telemetry_gateway
from ..adapter_dependencies import get_salinity_telemetry_gateway
from ..adapter_dependencies import get_imu_telemetry_gateway
from ..adapter_dependencies import get_ambient_light_telemetry_gateway
from ..adapter_dependencies import get_wind_telemetry_gateway
from ..adapter_dependencies import get_marine_current_telemetry_gateway
from ..adapter_dependencies import get_turbidity_telemetry_gateway
from ..adapter_dependencies import get_dissolved_oxygen_telemetry_gateway
from ..adapter_dependencies import get_ph_telemetry_gateway
from ..adapter_dependencies import get_conductivity_telemetry_gateway
from ..adapter_dependencies import get_chlorophyll_a_telemetry_gateway
from ..adapter_dependencies import get_rainfall_telemetry_gateway
from ..adapter_dependencies import get_humidity_telemetry_gateway
from ..adapter_dependencies import get_air_temperature_telemetry_gateway
from ..adapter_dependencies import get_atmospheric_pressure_telemetry_gateway
from ..adapter_dependencies import get_acoustic_altimeter_telemetry_gateway
from ..adapter_dependencies import get_underwater_acoustic_telemetry_gateway
from ..adapter_dependencies import get_sensor_health_reader
from ..adapter_dependencies import get_sensor_health_check_gateway
from ..adapter_dependencies import get_sensor_health_metrics
from ..adapter_dependencies import get_telemetry_metrics
from ..application.ambient_light_ports import AmbientLightTelemetryGateway
from ..application.ambient_light_ingestion import ingest_ambient_light_reading
from ..application.motion_ports import ImuTelemetryGateway
from ..application.motion_ingestion import ingest_imu_reading
from ..application.temperature_ingestion import ingest_temperature_reading
from ..application.pressure_ingestion import ingest_pressure_reading
from ..application.salinity_ingestion import ingest_salinity_reading
from ..application.turbidity_ingestion import ingest_turbidity_reading
from ..application.dissolved_oxygen_ingestion import ingest_dissolved_oxygen_reading
from ..application.ph_ingestion import ingest_ph_reading
from ..application.conductivity_ingestion import ingest_conductivity_reading
from ..application.flow_ports import MarineCurrentTelemetryGateway, WindTelemetryGateway
from ..application.marine_water_ports import (
    PressureTelemetryGateway,
    SalinityTelemetryGateway,
    TemperatureTelemetryGateway,
)
from ..application.acoustic_sensor_ports import (
    AcousticAltimeterTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
)
from ..application.weather_ports import (
    AirTemperatureTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
    HumidityTelemetryGateway,
    RainfallTelemetryGateway,
)
from ..application.water_quality_ports import (
    ChlorophyllATelemetryGateway,
    ConductivityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    PHTelemetryGateway,
    TurbidityTelemetryGateway,
)
from ..application.sensor_health_ports import (
    SensorHealthCheckGateway,
    SensorHealthMetrics,
    SensorHealthReader,
)
from ..application.telemetry_ports import TelemetryMetrics
from ..application.sensor_reading_metrics import record_sensor_reading_metrics
from ..application.sensor_health import (
    SensorHealthSnapshot as SensorHealthEvaluationSnapshot,
    evaluate_sensor_health_snapshot,
    persist_sensor_health_check,
)
from ..application.telemetry_ingestion import (
    build_acoustic_altimeter_snapshot,
    build_air_temperature_snapshot,
    build_ambient_light_snapshot,
    build_atmospheric_pressure_snapshot,
    build_chlorophyll_a_snapshot,
    build_conductivity_snapshot,
    build_dissolved_oxygen_snapshot,
    build_humidity_snapshot,
    build_imu_snapshot,
    build_marine_current_snapshot,
    build_ph_snapshot,
    build_pressure_snapshot,
    build_rainfall_snapshot,
    build_salinity_snapshot,
    build_temperature_snapshot,
    build_turbidity_snapshot,
    build_underwater_acoustic_snapshot,
    build_wind_snapshot,
)
from ..schemas.sensors import SensorHealth, SensorHealthCheck
from ..schemas.telemetry import (
    AcousticAltimeterReading,
    AcousticAltimeterReadingCreate,
    AirTemperatureReading,
    AirTemperatureReadingCreate,
    AmbientLightReading,
    AmbientLightReadingCreate,
    AtmosphericPressureReading,
    AtmosphericPressureReadingCreate,
    ChlorophyllAReading,
    ChlorophyllAReadingCreate,
    ConductivityReading,
    ConductivityReadingCreate,
    DissolvedOxygenReading,
    DissolvedOxygenReadingCreate,
    ImuReading,
    ImuReadingCreate,
    HumidityReading,
    HumidityReadingCreate,
    MarineCurrentReading,
    MarineCurrentReadingCreate,
    PressureReading,
    PressureReadingCreate,
    PHReading,
    PHReadingCreate,
    RainfallReading,
    RainfallReadingCreate,
    SalinityReading,
    SalinityReadingCreate,
    TemperatureReading,
    TemperatureReadingCreate,
    TurbidityReading,
    TurbidityReadingCreate,
    UnderwaterAcousticReading,
    UnderwaterAcousticReadingCreate,
    WindReading,
    WindReadingCreate,
)
router = APIRouter()


def record_buoy_heartbeat(metrics: TelemetryMetrics, buoy_id: str) -> None:
    """Record receipt time so sensor clock drift cannot fake buoy downtime."""
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(buoy_id=buoy_id).set(
        datetime.now(timezone.utc).timestamp()
    )


def _evaluate_and_publish_sensor_health(
    reader: SensorHealthReader,
    metrics: SensorHealthMetrics,
    buoy_id: str,
    max_age_minutes: float,
) -> SensorHealthEvaluationSnapshot:
    snapshot = evaluate_sensor_health_snapshot(
        reader,
        buoy_id,
        max_age_minutes * 60,
        datetime.now(timezone.utc),
    )
    metrics.record_evaluation(
        buoy_id,
        snapshot.readings,
        snapshot.evaluation.degraded_sensors,
        snapshot.evaluation.missing_sensors,
        snapshot.evaluation.decisions,
    )
    return snapshot


@router.get("/api/v1/buoys/{buoy_id}/sensor-health/history", response_model=list[SensorHealthCheck], tags=["sensors"])
def sensor_health_history(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    reader: SensorHealthReader = Depends(get_sensor_health_reader),
) -> list[SensorHealthCheck]:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return [
        SensorHealthCheck.model_validate(check, from_attributes=True)
        for check in reader.list_sensor_health_checks(buoy_id, limit)
    ]


@router.post("/api/v1/buoys/{buoy_id}/wind", response_model=WindReading, status_code=status.HTTP_201_CREATED, tags=["wind"])
def record_wind(
    buoy_id: str,
    payload: WindReadingCreate,
    gateway: WindTelemetryGateway = Depends(get_wind_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> WindReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_wind_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_wind(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics,
        buoy_id,
        "wind",
        reading.sensor_channel,
        reading.quality,
        {
            "wind_speed_mps": reading.wind_speed_mps,
            "wind_direction_degrees": reading.wind_direction_degrees,
        },
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/wind", response_model=list[WindReading], tags=["wind"])
def list_wind(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: WindTelemetryGateway = Depends(get_wind_telemetry_gateway),
) -> list[WindReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_wind(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/ambient-light", response_model=AmbientLightReading, status_code=status.HTTP_201_CREATED, tags=["ambient-light"])
def record_ambient_light(
    buoy_id: str,
    payload: AmbientLightReadingCreate,
    gateway: AmbientLightTelemetryGateway = Depends(get_ambient_light_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> AmbientLightReading:
    reading = build_ambient_light_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_ambient_light_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/ambient-light", response_model=list[AmbientLightReading], tags=["ambient-light"])
def list_ambient_light(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: AmbientLightTelemetryGateway = Depends(get_ambient_light_telemetry_gateway),
) -> list[AmbientLightReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_ambient_light(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/imu", response_model=ImuReading, status_code=status.HTTP_201_CREATED, tags=["imu"])
def record_imu(
    buoy_id: str,
    payload: ImuReadingCreate,
    gateway: ImuTelemetryGateway = Depends(get_imu_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> ImuReading:
    reading = build_imu_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_imu_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/imu", response_model=list[ImuReading], tags=["imu"])
def list_imu(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: ImuTelemetryGateway = Depends(get_imu_telemetry_gateway),
) -> list[ImuReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_imu(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/temperatures", response_model=TemperatureReading, status_code=status.HTTP_201_CREATED, tags=["temperature"])
def record_temperature(
    buoy_id: str,
    payload: TemperatureReadingCreate,
    gateway: TemperatureTelemetryGateway = Depends(get_temperature_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> TemperatureReading:
    reading = build_temperature_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_temperature_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/temperatures", response_model=list[TemperatureReading], tags=["temperature"])
def list_temperatures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: TemperatureTelemetryGateway = Depends(get_temperature_telemetry_gateway),
) -> list[TemperatureReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_temperatures(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/pressures", response_model=PressureReading, status_code=status.HTTP_201_CREATED, tags=["pressure"])
def record_pressure(
    buoy_id: str,
    payload: PressureReadingCreate,
    gateway: PressureTelemetryGateway = Depends(get_pressure_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> PressureReading:
    reading = build_pressure_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_pressure_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/pressures", response_model=list[PressureReading], tags=["pressure"])
def list_pressures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: PressureTelemetryGateway = Depends(get_pressure_telemetry_gateway),
) -> list[PressureReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_pressures(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/salinity", response_model=SalinityReading, status_code=status.HTTP_201_CREATED, tags=["salinity"])
def record_salinity(
    buoy_id: str,
    payload: SalinityReadingCreate,
    gateway: SalinityTelemetryGateway = Depends(get_salinity_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> SalinityReading:
    reading = build_salinity_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_salinity_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/salinity", response_model=list[SalinityReading], tags=["salinity"])
def list_salinity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: SalinityTelemetryGateway = Depends(get_salinity_telemetry_gateway),
) -> list[SalinityReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_salinity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/marine-current", response_model=MarineCurrentReading, status_code=status.HTTP_201_CREATED, tags=["marine-current"])
def record_marine_current(
    buoy_id: str,
    payload: MarineCurrentReadingCreate,
    gateway: MarineCurrentTelemetryGateway = Depends(get_marine_current_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> MarineCurrentReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_marine_current_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_marine_current(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics, buoy_id, "marine_current", reading.sensor_channel, reading.quality,
        {"current_speed_mps": reading.current_speed_mps,
         "current_direction_degrees": reading.current_direction_degrees},
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/marine-current", response_model=list[MarineCurrentReading], tags=["marine-current"])
def list_marine_current(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: MarineCurrentTelemetryGateway = Depends(get_marine_current_telemetry_gateway),
) -> list[MarineCurrentReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_marine_current(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/turbidity", response_model=TurbidityReading, status_code=status.HTTP_201_CREATED, tags=["turbidity"])
def record_turbidity(
    buoy_id: str,
    payload: TurbidityReadingCreate,
    gateway: TurbidityTelemetryGateway = Depends(get_turbidity_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> TurbidityReading:
    reading = build_turbidity_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_turbidity_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/turbidity", response_model=list[TurbidityReading], tags=["turbidity"])
def list_turbidity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: TurbidityTelemetryGateway = Depends(get_turbidity_telemetry_gateway),
) -> list[TurbidityReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_turbidity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/dissolved-oxygen", response_model=DissolvedOxygenReading, status_code=status.HTTP_201_CREATED, tags=["dissolved-oxygen"])
def record_dissolved_oxygen(
    buoy_id: str,
    payload: DissolvedOxygenReadingCreate,
    gateway: DissolvedOxygenTelemetryGateway = Depends(get_dissolved_oxygen_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> DissolvedOxygenReading:
    reading = build_dissolved_oxygen_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_dissolved_oxygen_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/dissolved-oxygen", response_model=list[DissolvedOxygenReading], tags=["dissolved-oxygen"])
def list_dissolved_oxygen(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: DissolvedOxygenTelemetryGateway = Depends(get_dissolved_oxygen_telemetry_gateway),
) -> list[DissolvedOxygenReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_dissolved_oxygen(buoy_id, limit, sensor_channel)
@router.post("/api/v1/buoys/{buoy_id}/ph", response_model=PHReading, status_code=status.HTTP_201_CREATED, tags=["ph"])
def record_ph(
    buoy_id: str,
    payload: PHReadingCreate,
    gateway: PHTelemetryGateway = Depends(get_ph_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> PHReading:
    reading = build_ph_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_ph_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/ph", response_model=list[PHReading], tags=["ph"])
def list_ph(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: PHTelemetryGateway = Depends(get_ph_telemetry_gateway),
) -> list[PHReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_ph(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/conductivity", response_model=ConductivityReading, status_code=status.HTTP_201_CREATED, tags=["conductivity"])
def record_conductivity(
    buoy_id: str,
    payload: ConductivityReadingCreate,
    gateway: ConductivityTelemetryGateway = Depends(get_conductivity_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> ConductivityReading:
    reading = build_conductivity_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = ingest_conductivity_reading(gateway, metrics, reading)
    if saved_reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/conductivity", response_model=list[ConductivityReading], tags=["conductivity"])
def list_conductivity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: ConductivityTelemetryGateway = Depends(get_conductivity_telemetry_gateway),
) -> list[ConductivityReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_conductivity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/chlorophyll-a", response_model=ChlorophyllAReading, status_code=status.HTTP_201_CREATED, tags=["chlorophyll-a"])
def record_chlorophyll_a(
    buoy_id: str,
    payload: ChlorophyllAReadingCreate,
    gateway: ChlorophyllATelemetryGateway = Depends(get_chlorophyll_a_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> ChlorophyllAReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_chlorophyll_a_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_chlorophyll_a(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics, buoy_id, "chlorophyll_a", reading.sensor_channel, reading.quality,
        {"chlorophyll_a_ug_l": reading.chlorophyll_a_ug_l},
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/chlorophyll-a", response_model=list[ChlorophyllAReading], tags=["chlorophyll-a"])
def list_chlorophyll_a(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: ChlorophyllATelemetryGateway = Depends(get_chlorophyll_a_telemetry_gateway),
) -> list[ChlorophyllAReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_chlorophyll_a(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/rainfall", response_model=RainfallReading, status_code=status.HTTP_201_CREATED, tags=["rainfall"])
def record_rainfall(
    buoy_id: str,
    payload: RainfallReadingCreate,
    gateway: RainfallTelemetryGateway = Depends(get_rainfall_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> RainfallReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_rainfall_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_rainfall(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(metrics, buoy_id, "rainfall", reading.sensor_channel,
                                  reading.quality, {"rainfall_mm_h": reading.rainfall_mm_h})
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/rainfall", response_model=list[RainfallReading], tags=["rainfall"])
def list_rainfall(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: RainfallTelemetryGateway = Depends(get_rainfall_telemetry_gateway),
) -> list[RainfallReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_rainfall(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/humidity", response_model=HumidityReading, status_code=status.HTTP_201_CREATED, tags=["humidity"])
def record_humidity(
    buoy_id: str,
    payload: HumidityReadingCreate,
    gateway: HumidityTelemetryGateway = Depends(get_humidity_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> HumidityReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_humidity_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_humidity(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(metrics, buoy_id, "humidity", reading.sensor_channel,
                                  reading.quality, {"humidity_percent": reading.humidity_percent})
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/humidity", response_model=list[HumidityReading], tags=["humidity"])
def list_humidity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: HumidityTelemetryGateway = Depends(get_humidity_telemetry_gateway),
) -> list[HumidityReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_humidity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/air-temperature", response_model=AirTemperatureReading, status_code=status.HTTP_201_CREATED, tags=["air-temperature"])
def record_air_temperature(
    buoy_id: str,
    payload: AirTemperatureReadingCreate,
    gateway: AirTemperatureTelemetryGateway = Depends(get_air_temperature_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> AirTemperatureReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_air_temperature_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_air_temperature(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics, buoy_id, "air_temperature", reading.sensor_channel, reading.quality,
        {"air_temperature_celsius": reading.air_temperature_celsius},
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/air-temperature", response_model=list[AirTemperatureReading], tags=["air-temperature"])
def list_air_temperature(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: AirTemperatureTelemetryGateway = Depends(get_air_temperature_telemetry_gateway),
) -> list[AirTemperatureReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_air_temperature(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/atmospheric-pressure", response_model=AtmosphericPressureReading, status_code=status.HTTP_201_CREATED, tags=["atmospheric-pressure"])
def record_atmospheric_pressure(
    buoy_id: str,
    payload: AtmosphericPressureReadingCreate,
    gateway: AtmosphericPressureTelemetryGateway = Depends(get_atmospheric_pressure_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> AtmosphericPressureReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_atmospheric_pressure_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_atmospheric_pressure(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics, buoy_id, "atmospheric_pressure", reading.sensor_channel,
        reading.quality, {"atmospheric_pressure_kpa": reading.atmospheric_pressure_kpa},
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/atmospheric-pressure", response_model=list[AtmosphericPressureReading], tags=["atmospheric-pressure"])
def list_atmospheric_pressure(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: AtmosphericPressureTelemetryGateway = Depends(get_atmospheric_pressure_telemetry_gateway),
) -> list[AtmosphericPressureReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_atmospheric_pressure(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/acoustic-altimeter", response_model=AcousticAltimeterReading, status_code=status.HTTP_201_CREATED, tags=["acoustic-altimeter"])
def record_acoustic_altimeter(
    buoy_id: str,
    payload: AcousticAltimeterReadingCreate,
    gateway: AcousticAltimeterTelemetryGateway = Depends(get_acoustic_altimeter_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> AcousticAltimeterReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_acoustic_altimeter_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_acoustic_altimeter(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics, buoy_id, "acoustic_altimeter", reading.sensor_channel,
        reading.quality, {"depth_meters": reading.depth_meters},
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/acoustic-altimeter", response_model=list[AcousticAltimeterReading], tags=["acoustic-altimeter"])
def list_acoustic_altimeter(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: AcousticAltimeterTelemetryGateway = Depends(get_acoustic_altimeter_telemetry_gateway),
) -> list[AcousticAltimeterReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_acoustic_altimeter(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/underwater-acoustic", response_model=UnderwaterAcousticReading, status_code=status.HTTP_201_CREATED, tags=["underwater-acoustic"])
def record_underwater_acoustic(
    buoy_id: str,
    payload: UnderwaterAcousticReadingCreate,
    gateway: UnderwaterAcousticTelemetryGateway = Depends(get_underwater_acoustic_telemetry_gateway),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> UnderwaterAcousticReading:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = build_underwater_acoustic_snapshot(buoy_id, payload.model_dump(), None)
    saved_reading = gateway.add_underwater_acoustic(reading)
    record_buoy_heartbeat(metrics, buoy_id)
    record_sensor_reading_metrics(
        metrics, buoy_id, "underwater_acoustic", reading.sensor_channel,
        reading.quality, {"echo_intensity_db": reading.echo_intensity_db},
    )
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/underwater-acoustic", response_model=list[UnderwaterAcousticReading], tags=["underwater-acoustic"])
def list_underwater_acoustic(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    gateway: UnderwaterAcousticTelemetryGateway = Depends(get_underwater_acoustic_telemetry_gateway),
) -> list[UnderwaterAcousticReading]:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return gateway.list_underwater_acoustic(buoy_id, limit, sensor_channel)
@router.get(
    "/api/v1/buoys/{buoy_id}/sensor-health",
    response_model=SensorHealth,
    tags=["sensors"],
)
def sensor_health(
    buoy_id: str,
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    reader: SensorHealthReader = Depends(get_sensor_health_reader),
    metrics: SensorHealthMetrics = Depends(get_sensor_health_metrics),
) -> SensorHealth:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    snapshot = _evaluate_and_publish_sensor_health(
        reader, metrics, buoy_id, max_age_minutes
    )
    return SensorHealth.model_validate(snapshot.health, from_attributes=True)


@router.post(
    "/api/v1/buoys/{buoy_id}/sensor-health/check",
    response_model=SensorHealthCheck,
    status_code=status.HTTP_201_CREATED,
    tags=["sensors"],
)
def record_sensor_health_check(
    buoy_id: str,
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    gateway: SensorHealthCheckGateway = Depends(get_sensor_health_check_gateway),
    metrics: SensorHealthMetrics = Depends(get_sensor_health_metrics),
) -> SensorHealthCheck:
    if not gateway.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    snapshot = _evaluate_and_publish_sensor_health(
        gateway, metrics, buoy_id, max_age_minutes
    )
    stored = persist_sensor_health_check(gateway, snapshot.health)
    return SensorHealthCheck.model_validate(stored, from_attributes=True)
