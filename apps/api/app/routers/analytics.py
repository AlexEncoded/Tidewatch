"""HTTP routes for buoy analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..application.movement_analysis import analyze_movement_for_buoy
from ..application.pressure_analysis import analyze_pressure_for_buoy
from ..application.temperature_analysis import (
    analyze_temperature_for_buoy,
)
from ..application.temperature_alerts import find_temperature_anomalies
from ..application.wave_analysis import analyze_wave_for_buoy, configured_wave_imu_factor
from ..adapter_dependencies import (
    get_movement_analysis_reader,
    get_pressure_analysis_reader,
    get_wave_analysis_reader,
    get_temperature_analysis_reader,
    get_temperature_alerts_reader,
)
from ..application.ports import (
    MovementAnalysisReader,
    PressureAnalysisReader,
    TemperatureAnalysisReader,
    TemperatureAlertsReader,
    WaveAnalysisReader,
)
from ..metrics import current_estimated_wave_height_m, current_estimated_wave_period_seconds
from ..schemas.analytics import (
    MovementAnalysis,
    PressureAnalysis,
    TemperatureAlert,
    TemperatureAnalysis,
    WaveAnalysis,
)
router = APIRouter()


@router.get("/api/v1/buoys/{buoy_id}/pressure-analysis", response_model=PressureAnalysis, tags=["pressure"])
def pressure_analysis(
    buoy_id: str,
    window: int = Query(default=50, ge=1, le=500),
    reader: PressureAnalysisReader = Depends(get_pressure_analysis_reader),
) -> PressureAnalysis:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_pressure_for_buoy(reader, buoy_id, window)
    return PressureAnalysis.model_validate(result, from_attributes=True)


@router.get("/api/v1/buoys/{buoy_id}/movement-analysis", response_model=MovementAnalysis, tags=["buoys"])
def buoy_movement_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    reader: MovementAnalysisReader = Depends(get_movement_analysis_reader),
) -> MovementAnalysis:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_movement_for_buoy(reader, buoy_id, window)
    return MovementAnalysis.model_validate(result, from_attributes=True)


@router.get("/api/v1/buoys/{buoy_id}/wave-analysis", response_model=WaveAnalysis, tags=["analytics"])
def buoy_wave_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    reader: WaveAnalysisReader = Depends(get_wave_analysis_reader),
) -> WaveAnalysis:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_wave_for_buoy(reader, buoy_id, window, configured_wave_imu_factor())
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
    return WaveAnalysis.model_validate(result, from_attributes=True)


@router.get(
    "/api/v1/buoys/{buoy_id}/temperature-analysis",
    response_model=TemperatureAnalysis,
    tags=["temperature"],
)
def temperature_analysis(
    buoy_id: str,
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    reader: TemperatureAnalysisReader = Depends(get_temperature_analysis_reader),
) -> TemperatureAnalysis:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_temperature_for_buoy(reader, buoy_id, window, threshold)
    return TemperatureAnalysis.model_validate(result, from_attributes=True)


@router.get(
    "/api/v1/alerts/temperature",
    response_model=list[TemperatureAlert],
    tags=["alerts"],
)
def temperature_alerts(
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    reader: TemperatureAlertsReader = Depends(get_temperature_alerts_reader),
) -> list[TemperatureAlert]:
    return [
        TemperatureAlert.model_validate(alert, from_attributes=True)
        for alert in find_temperature_anomalies(reader, threshold, window)
    ]
