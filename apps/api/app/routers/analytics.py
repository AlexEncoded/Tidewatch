"""HTTP routes for buoy analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.movement_analysis import analyze_movement_for_buoy
from ..application.temperature_analysis import analyze_temperature_for_buoy
from ..application.wave_analysis import analyze_wave_for_buoy, configured_wave_imu_factor
from ..database import get_db
from ..metrics import current_estimated_wave_height_m, current_estimated_wave_period_seconds
from ..models import MovementAnalysis, TemperatureAnalysis, WaveAnalysis
from ..repository import BuoyRepository


router = APIRouter()


@router.get("/api/v1/buoys/{buoy_id}/movement-analysis", response_model=MovementAnalysis, tags=["buoys"])
def buoy_movement_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    db: Session = Depends(get_db),
) -> MovementAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return analyze_movement_for_buoy(repository, buoy_id, window)


@router.get("/api/v1/buoys/{buoy_id}/wave-analysis", response_model=WaveAnalysis, tags=["analytics"])
def buoy_wave_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    db: Session = Depends(get_db),
) -> WaveAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_wave_for_buoy(repository, buoy_id, window, configured_wave_imu_factor())
    if result.estimated_wave_height_m is not None:
        current_estimated_wave_height_m.labels(buoy_id=buoy_id).set(result.estimated_wave_height_m)
    else:
        try:
            current_estimated_wave_height_m.remove(buoy_id)
        except KeyError:
            pass
    if result.estimated_period_seconds is not None:
        current_estimated_wave_period_seconds.labels(buoy_id=buoy_id).set(result.estimated_period_seconds)
    else:
        try:
            current_estimated_wave_period_seconds.remove(buoy_id)
        except KeyError:
            pass
    return result


@router.get(
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
