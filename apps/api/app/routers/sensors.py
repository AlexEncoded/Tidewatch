"""Specialized sensor telemetry endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..metrics import (
    acoustic_altimeter_readings_total,
    atmospheric_pressure_readings_total,
    current_acoustic_altimeter_depth_meters,
    current_atmospheric_pressure_kpa,
    current_underwater_acoustic_echo_intensity_db,
    reading_quality_total,
    underwater_acoustic_readings_total,
)
from ..models import (
    AcousticAltimeterReading,
    AcousticAltimeterReadingCreate,
    AtmosphericPressureReading,
    AtmosphericPressureReadingCreate,
    UnderwaterAcousticReading,
    UnderwaterAcousticReadingCreate,
)
from ..repository import BuoyRepository

router = APIRouter()


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
