"""Specialized sensor telemetry endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..metrics import (
    acoustic_altimeter_readings_total,
    atmospheric_pressure_readings_total,
    air_temperature_readings_total,
    humidity_readings_total,
    chlorophyll_a_readings_total,
    conductivity_readings_total,
    rainfall_readings_total,
    current_acoustic_altimeter_depth_meters,
    current_air_temperature_celsius,
    current_dissolved_oxygen_mg_l,
    current_turbidity_ntu,
    current_atmospheric_pressure_kpa,
    current_humidity_percent,
    current_marine_current_direction_degrees,
    current_marine_current_speed_mps,
    current_ph,
    current_chlorophyll_a_ug_l,
    current_conductivity_us_cm,
    ph_readings_total,
    current_rainfall_mm_h,
    dissolved_oxygen_readings_total,
    marine_current_readings_total,
    turbidity_readings_total,
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
