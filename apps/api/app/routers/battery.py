"""Battery telemetry and health endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.battery_analysis import analyze_battery_for_buoy
from ..application.battery_health import analyze_battery_health_for_buoy
from ..database import get_db
from ..metrics import battery_delta_percent, battery_device_percent, battery_percent
from ..models import BatteryAnalysis, BatteryHealth, BatteryReading, BatteryReadingCreate
from ..repository import BuoyRepository

router = APIRouter()


def get_battery_repository(buoy_id: str, db: Session) -> BuoyRepository:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository


@router.post("/api/v1/buoys/{buoy_id}/battery", response_model=BatteryReading, status_code=status.HTTP_201_CREATED, tags=["battery"])
def record_battery(buoy_id: str, payload: BatteryReadingCreate, db: Session = Depends(get_db)) -> BatteryReading:
    repository = get_battery_repository(buoy_id, db)
    battery = BatteryReading(buoy_id=buoy_id, **payload.model_dump())
    saved_battery = repository.add_battery(battery)
    battery_percent.labels(buoy_id=buoy_id).set(battery.battery_percent)
    return saved_battery


@router.get("/api/v1/buoys/{buoy_id}/battery", response_model=BatteryReading | None, tags=["battery"])
def latest_battery(buoy_id: str, device_id: str | None = Query(default=None, pattern="^(A|B)$"), db: Session = Depends(get_db)) -> BatteryReading | None:
    repository = get_battery_repository(buoy_id, db)
    return repository.latest_battery(buoy_id, device_id)


@router.get("/api/v1/buoys/{buoy_id}/battery/history", response_model=list[BatteryReading], tags=["battery"])
def battery_history(buoy_id: str, limit: int = Query(default=100, ge=1, le=500), device_id: str | None = Query(default=None, pattern="^(A|B)$"), db: Session = Depends(get_db)) -> list[BatteryReading]:
    repository = get_battery_repository(buoy_id, db)
    return repository.list_batteries(buoy_id, limit, device_id)


@router.get("/api/v1/buoys/{buoy_id}/battery-analysis", response_model=BatteryAnalysis, tags=["battery"])
def battery_analysis(buoy_id: str, device_id: str = Query(default="A", pattern="^(A|B)$"), window: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> BatteryAnalysis:
    repository = get_battery_repository(buoy_id, db)
    return analyze_battery_for_buoy(repository, buoy_id, device_id, window)


@router.get("/api/v1/buoys/{buoy_id}/battery-health", response_model=BatteryHealth, tags=["battery"])
def battery_health(buoy_id: str, threshold: float = Query(default=10, gt=0, le=100), db: Session = Depends(get_db)) -> BatteryHealth:
    repository = get_battery_repository(buoy_id, db)
    result = analyze_battery_health_for_buoy(repository, buoy_id, threshold)
    for device_id, percentage in (("A", result.device_a_percent), ("B", result.device_b_percent)):
        if percentage is not None:
            battery_device_percent.labels(buoy_id=buoy_id, device_id=device_id).set(percentage)
    if result.delta_percent is not None:
        battery_delta_percent.labels(buoy_id=buoy_id).set(result.delta_percent)
    return result
