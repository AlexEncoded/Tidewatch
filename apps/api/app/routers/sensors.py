"""Specialized sensor telemetry endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..application.sensor_health import (
    evaluate_sensor_health_snapshot,
    persist_sensor_health_check,
)
from ..metrics import (
    acoustic_altimeter_readings_total,
    atmospheric_pressure_readings_total,
    air_temperature_readings_total,
    buoy_last_seen_timestamp_seconds,
    humidity_readings_total,
    chlorophyll_a_readings_total,
    conductivity_readings_total,
    rainfall_readings_total,
    salinity_readings_total,
    current_acoustic_altimeter_depth_meters,
    current_air_temperature_celsius,
    current_dissolved_oxygen_mg_l,
    current_turbidity_ntu,
    current_atmospheric_pressure_kpa,
    current_humidity_percent,
    current_marine_current_direction_degrees,
    current_marine_current_speed_mps,
    current_temperature_celsius,
    current_pressure_kpa,
    current_salinity_psu,
    current_imu_acceleration_mps2,
    current_imu_angular_velocity_dps,
    current_ambient_light_lux,
    current_wind_speed_mps,
    current_wind_direction_degrees,
    sensor_channel_missing,
    sensor_degraded,
    sensor_health_decision,
    current_ph,
    current_chlorophyll_a_ug_l,
    current_conductivity_us_cm,
    ph_readings_total,
    pressure_readings_total,
    current_rainfall_mm_h,
    dissolved_oxygen_readings_total,
    marine_current_readings_total,
    turbidity_readings_total,
    temperature_readings_total,
    imu_readings_total,
    ambient_light_readings_total,
    wind_readings_total,
    current_underwater_acoustic_echo_intensity_db,
    reading_quality_total,
    underwater_acoustic_readings_total,
)
from ..models import (
    AcousticAltimeterReading,
    AcousticAltimeterReadingCreate,
    AtmosphericPressureReading,
    AtmosphericPressureReadingCreate,
    AirTemperatureReading,
    AirTemperatureReadingCreate,
    HumidityReading,
    HumidityReadingCreate,
    MarineCurrentReading,
    MarineCurrentReadingCreate,
    TemperatureReading,
    TemperatureReadingCreate,
    PressureReading,
    PressureReadingCreate,
    SalinityReading,
    SalinityReadingCreate,
    ImuReading,
    ImuReadingCreate,
    AmbientLightReading,
    AmbientLightReadingCreate,
    WindReading,
    WindReadingCreate,
    SensorHealthCheck,
    SensorHealth,
    ChlorophyllAReading,
    ChlorophyllAReadingCreate,
    ConductivityReading,
    ConductivityReadingCreate,
    DissolvedOxygenReading,
    DissolvedOxygenReadingCreate,
    TurbidityReading,
    TurbidityReadingCreate,
    PHReading,
    PHReadingCreate,
    RainfallReading,
    RainfallReadingCreate,
    UnderwaterAcousticReading,
    UnderwaterAcousticReadingCreate,
)
from ..repository import BuoyRepository

router = APIRouter()


@router.get("/api/v1/buoys/{buoy_id}/sensor-health/history", response_model=list[SensorHealthCheck], tags=["sensors"])
def sensor_health_history(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> list[SensorHealthCheck]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_sensor_health_checks(buoy_id, limit)


@router.post("/api/v1/buoys/{buoy_id}/wind", response_model=WindReading, status_code=status.HTTP_201_CREATED, tags=["wind"])
def record_wind(buoy_id: str, payload: WindReadingCreate, db: Session = Depends(get_db)) -> WindReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = WindReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_wind(reading)
    wind_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_wind_speed_mps.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.wind_speed_mps)
    current_wind_direction_degrees.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.wind_direction_degrees)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="wind", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/wind", response_model=list[WindReading], tags=["wind"])
def list_wind(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[WindReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_wind(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/ambient-light", response_model=AmbientLightReading, status_code=status.HTTP_201_CREATED, tags=["ambient-light"])
def record_ambient_light(buoy_id: str, payload: AmbientLightReadingCreate, db: Session = Depends(get_db)) -> AmbientLightReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AmbientLightReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_ambient_light(reading)
    ambient_light_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_ambient_light_lux.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.illuminance_lux)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="ambient_light", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/ambient-light", response_model=list[AmbientLightReading], tags=["ambient-light"])
def list_ambient_light(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AmbientLightReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_ambient_light(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/imu", response_model=ImuReading, status_code=status.HTTP_201_CREATED, tags=["imu"])
def record_imu(buoy_id: str, payload: ImuReadingCreate, db: Session = Depends(get_db)) -> ImuReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = ImuReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_imu(reading)
    imu_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    for axis, value in {"x": reading.acceleration_x_mps2, "y": reading.acceleration_y_mps2, "z": reading.acceleration_z_mps2}.items():
        current_imu_acceleration_mps2.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel, axis=axis).set(value)
    for axis, value in {"x": reading.angular_velocity_x_dps, "y": reading.angular_velocity_y_dps, "z": reading.angular_velocity_z_dps}.items():
        current_imu_angular_velocity_dps.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel, axis=axis).set(value)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="imu", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/imu", response_model=list[ImuReading], tags=["imu"])
def list_imu(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[ImuReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_imu(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/temperatures", response_model=TemperatureReading, status_code=status.HTTP_201_CREATED, tags=["temperature"])
def record_temperature(buoy_id: str, payload: TemperatureReadingCreate, db: Session = Depends(get_db)) -> TemperatureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = TemperatureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_temperature(reading)
    temperature_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_temperature_celsius.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.temperature_celsius)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="temperature", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(reading.measured_at.timestamp())
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/temperatures", response_model=list[TemperatureReading], tags=["temperature"])
def list_temperatures(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[TemperatureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_temperatures(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/pressures", response_model=PressureReading, status_code=status.HTTP_201_CREATED, tags=["pressure"])
def record_pressure(buoy_id: str, payload: PressureReadingCreate, db: Session = Depends(get_db)) -> PressureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = PressureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_pressure(reading)
    pressure_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_pressure_kpa.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.pressure_kpa)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="pressure", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/pressures", response_model=list[PressureReading], tags=["pressure"])
def list_pressures(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[PressureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_pressures(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/salinity", response_model=SalinityReading, status_code=status.HTTP_201_CREATED, tags=["salinity"])
def record_salinity(buoy_id: str, payload: SalinityReadingCreate, db: Session = Depends(get_db)) -> SalinityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = SalinityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_salinity(reading)
    salinity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_salinity_psu.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.salinity_psu)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="salinity", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/salinity", response_model=list[SalinityReading], tags=["salinity"])
def list_salinity(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[SalinityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_salinity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/marine-current", response_model=MarineCurrentReading, status_code=status.HTTP_201_CREATED, tags=["marine-current"])
def record_marine_current(buoy_id: str, payload: MarineCurrentReadingCreate, db: Session = Depends(get_db)) -> MarineCurrentReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = MarineCurrentReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_marine_current(reading)
    marine_current_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_marine_current_speed_mps.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.current_speed_mps)
    current_marine_current_direction_degrees.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.current_direction_degrees)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="marine_current", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/marine-current", response_model=list[MarineCurrentReading], tags=["marine-current"])
def list_marine_current(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[MarineCurrentReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_marine_current(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/turbidity", response_model=TurbidityReading, status_code=status.HTTP_201_CREATED, tags=["turbidity"])
def record_turbidity(buoy_id: str, payload: TurbidityReadingCreate, db: Session = Depends(get_db)) -> TurbidityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = TurbidityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_turbidity(reading)
    turbidity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_turbidity_ntu.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.turbidity_ntu)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="turbidity", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/turbidity", response_model=list[TurbidityReading], tags=["turbidity"])
def list_turbidity(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[TurbidityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_turbidity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/dissolved-oxygen", response_model=DissolvedOxygenReading, status_code=status.HTTP_201_CREATED, tags=["dissolved-oxygen"])
def record_dissolved_oxygen(buoy_id: str, payload: DissolvedOxygenReadingCreate, db: Session = Depends(get_db)) -> DissolvedOxygenReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = DissolvedOxygenReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_dissolved_oxygen(reading)
    dissolved_oxygen_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_dissolved_oxygen_mg_l.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.dissolved_oxygen_mg_l)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="dissolved_oxygen", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/dissolved-oxygen", response_model=list[DissolvedOxygenReading], tags=["dissolved-oxygen"])
def list_dissolved_oxygen(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[DissolvedOxygenReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_dissolved_oxygen(buoy_id, limit, sensor_channel)
@router.post("/api/v1/buoys/{buoy_id}/ph", response_model=PHReading, status_code=status.HTTP_201_CREATED, tags=["ph"])
def record_ph(buoy_id: str, payload: PHReadingCreate, db: Session = Depends(get_db)) -> PHReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = PHReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_ph(reading)
    ph_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_ph.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.ph)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="ph", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/ph", response_model=list[PHReading], tags=["ph"])
def list_ph(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[PHReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_ph(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/conductivity", response_model=ConductivityReading, status_code=status.HTTP_201_CREATED, tags=["conductivity"])
def record_conductivity(buoy_id: str, payload: ConductivityReadingCreate, db: Session = Depends(get_db)) -> ConductivityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = ConductivityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_conductivity(reading)
    conductivity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_conductivity_us_cm.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.conductivity_us_cm)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="conductivity", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/conductivity", response_model=list[ConductivityReading], tags=["conductivity"])
def list_conductivity(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[ConductivityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_conductivity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/chlorophyll-a", response_model=ChlorophyllAReading, status_code=status.HTTP_201_CREATED, tags=["chlorophyll-a"])
def record_chlorophyll_a(buoy_id: str, payload: ChlorophyllAReadingCreate, db: Session = Depends(get_db)) -> ChlorophyllAReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = ChlorophyllAReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_chlorophyll_a(reading)
    chlorophyll_a_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_chlorophyll_a_ug_l.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.chlorophyll_a_ug_l)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="chlorophyll_a", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/chlorophyll-a", response_model=list[ChlorophyllAReading], tags=["chlorophyll-a"])
def list_chlorophyll_a(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[ChlorophyllAReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_chlorophyll_a(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/rainfall", response_model=RainfallReading, status_code=status.HTTP_201_CREATED, tags=["rainfall"])
def record_rainfall(buoy_id: str, payload: RainfallReadingCreate, db: Session = Depends(get_db)) -> RainfallReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = RainfallReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_rainfall(reading)
    rainfall_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_rainfall_mm_h.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.rainfall_mm_h)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="rainfall", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/rainfall", response_model=list[RainfallReading], tags=["rainfall"])
def list_rainfall(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[RainfallReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_rainfall(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/humidity", response_model=HumidityReading, status_code=status.HTTP_201_CREATED, tags=["humidity"])
def record_humidity(buoy_id: str, payload: HumidityReadingCreate, db: Session = Depends(get_db)) -> HumidityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = HumidityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_humidity(reading)
    humidity_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_humidity_percent.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.humidity_percent)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="humidity", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/humidity", response_model=list[HumidityReading], tags=["humidity"])
def list_humidity(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[HumidityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_humidity(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/air-temperature", response_model=AirTemperatureReading, status_code=status.HTTP_201_CREATED, tags=["air-temperature"])
def record_air_temperature(buoy_id: str, payload: AirTemperatureReadingCreate, db: Session = Depends(get_db)) -> AirTemperatureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AirTemperatureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_air_temperature(reading)
    air_temperature_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_air_temperature_celsius.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.air_temperature_celsius)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="air_temperature", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/air-temperature", response_model=list[AirTemperatureReading], tags=["air-temperature"])
def list_air_temperature(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AirTemperatureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_air_temperature(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/atmospheric-pressure", response_model=AtmosphericPressureReading, status_code=status.HTTP_201_CREATED, tags=["atmospheric-pressure"])
def record_atmospheric_pressure(buoy_id: str, payload: AtmosphericPressureReadingCreate, db: Session = Depends(get_db)) -> AtmosphericPressureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AtmosphericPressureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_atmospheric_pressure(reading)
    atmospheric_pressure_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_atmospheric_pressure_kpa.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.atmospheric_pressure_kpa)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="atmospheric_pressure", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/atmospheric-pressure", response_model=list[AtmosphericPressureReading], tags=["atmospheric-pressure"])
def list_atmospheric_pressure(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AtmosphericPressureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_atmospheric_pressure(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/acoustic-altimeter", response_model=AcousticAltimeterReading, status_code=status.HTTP_201_CREATED, tags=["acoustic-altimeter"])
def record_acoustic_altimeter(buoy_id: str, payload: AcousticAltimeterReadingCreate, db: Session = Depends(get_db)) -> AcousticAltimeterReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = AcousticAltimeterReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_acoustic_altimeter(reading)
    acoustic_altimeter_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_acoustic_altimeter_depth_meters.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.depth_meters)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="acoustic_altimeter", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/acoustic-altimeter", response_model=list[AcousticAltimeterReading], tags=["acoustic-altimeter"])
def list_acoustic_altimeter(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[AcousticAltimeterReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_acoustic_altimeter(buoy_id, limit, sensor_channel)


@router.post("/api/v1/buoys/{buoy_id}/underwater-acoustic", response_model=UnderwaterAcousticReading, status_code=status.HTTP_201_CREATED, tags=["underwater-acoustic"])
def record_underwater_acoustic(buoy_id: str, payload: UnderwaterAcousticReadingCreate, db: Session = Depends(get_db)) -> UnderwaterAcousticReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = UnderwaterAcousticReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_underwater_acoustic(reading)
    underwater_acoustic_readings_total.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
    current_underwater_acoustic_echo_intensity_db.labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.echo_intensity_db)
    reading_quality_total.labels(buoy_id=buoy_id, sensor_family="underwater_acoustic", sensor_channel=reading.sensor_channel, quality=reading.quality).inc()
    return saved_reading


@router.get("/api/v1/buoys/{buoy_id}/underwater-acoustic", response_model=list[UnderwaterAcousticReading], tags=["underwater-acoustic"])
def list_underwater_acoustic(buoy_id: str, limit: int = Query(default=50, ge=1, le=500), sensor_channel: str = Query(default="A", pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[UnderwaterAcousticReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_underwater_acoustic(buoy_id, limit, sensor_channel)
@router.get(
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
    snapshot = evaluate_sensor_health_snapshot(
        repository, buoy_id, max_age_seconds, now
    )
    sensor_readings = snapshot.readings
    deltas = snapshot.deltas
    health_evaluation = snapshot.evaluation
    degraded_sensors = health_evaluation.degraded_sensors
    missing_sensors = health_evaluation.missing_sensors

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

    decisions = health_evaluation.decisions
    for sensor in sensor_readings:
        for decision in ("average", "fallback_a", "fallback_b", "invalid"):
            sensor_health_decision.labels(
                buoy_id=buoy_id, sensor=sensor, decision=decision
            ).set(1 if decisions[sensor] == decision else 0)
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
    db: Session = Depends(get_db),
) -> SensorHealthCheck:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    health = sensor_health(buoy_id, max_age_minutes=max_age_minutes, db=db)
    stored = persist_sensor_health_check(repository, health)
    return SensorHealthCheck.model_validate(stored, from_attributes=True)
