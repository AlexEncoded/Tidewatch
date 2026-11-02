"""HTTP routes for buoy analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..application.movement_analysis import analyze_movement_for_buoy
from ..application.pressure_analysis import analyze_pressure_for_buoy
from ..application.temperature_analysis import (
    analyze_temperature_for_buoy,
)
from ..application.temperature_alerts import find_temperature_anomalies
from ..application.wave_analysis import analyze_wave_for_buoy
from ..adapter_dependencies import (
    get_movement_analysis_reader,
    get_pressure_analysis_reader,
    get_wave_analysis_reader,
    get_wave_analysis_metrics,
    get_temperature_analysis_reader,
    get_temperature_alerts_reader,
)
from ..application.fleet_ports import MovementAnalysisReader
from ..application.analysis_ports import (
    PressureAnalysisReader,
    TemperatureAnalysisReader,
    WaveAnalysisMetrics,
    WaveAnalysisReader,
)
from ..application.alert_ports import TemperatureAlertsReader
from ..schemas.analytics import (
    MovementAnalysis,
    PressureAnalysis,
    TemperatureAlert,
    TemperatureAnalysis,
    WaveAnalysis,
)
from ..settings import configured_wave_imu_factor
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
    metrics: WaveAnalysisMetrics = Depends(get_wave_analysis_metrics),
) -> WaveAnalysis:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    result = analyze_wave_for_buoy(reader, buoy_id, window, configured_wave_imu_factor())
    metrics.record_analysis(result)
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
