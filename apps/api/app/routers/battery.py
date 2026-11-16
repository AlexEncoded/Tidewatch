"""Battery telemetry and health endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..application.battery_analysis import analyze_battery_for_buoy
from ..application.battery_ingestion import ingest_battery_reading
from ..application.battery_health import evaluate_battery_health_for_buoy
from ..application.battery_queries import (
    get_latest_battery,
    list_battery_history,
)
from ..application.battery_errors import (
    BatteryBuoyNotFound,
    BatteryDeviceNotFound,
    BatteryTelemetryInvalid,
)
from ..application.analysis_queries import analyze_if_buoy_exists
from ..application.telemetry_ingestion import build_battery_snapshot
from ..adapter_dependencies import get_battery_metrics, get_battery_telemetry_reader
from ..application.battery_ports import BatteryMetrics, BatteryTelemetryReader
from ..schemas.battery import (
    BatteryAnalysis,
    BatteryHealth,
    BatteryReading,
    BatteryReadingCreate,
)

router = APIRouter()


@router.post("/api/v1/buoys/{buoy_id}/battery", response_model=BatteryReading, status_code=status.HTTP_201_CREATED, tags=["battery"])
def record_battery(
    buoy_id: str,
    payload: BatteryReadingCreate,
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
    metrics: BatteryMetrics = Depends(get_battery_metrics),
) -> BatteryReading:
    battery = build_battery_snapshot(buoy_id, payload.model_dump())
    received_at = datetime.now(timezone.utc)
    try:
        saved_battery = ingest_battery_reading(reader, metrics, battery, received_at)
        if saved_battery is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    except BatteryDeviceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except BatteryTelemetryInvalid as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None
    return saved_battery


@router.get("/api/v1/buoys/{buoy_id}/battery", response_model=BatteryReading | None, tags=["battery"])
def latest_battery(
    buoy_id: str,
    device_id: str | None = Query(default=None, pattern="^(A|B)$"),
    physical_device_id: str | None = Query(default=None, min_length=1, max_length=100),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> BatteryReading | None:
    try:
        return get_latest_battery(reader, buoy_id, device_id, physical_device_id)
    except BatteryBuoyNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found"
        ) from None
    except BatteryDeviceNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from None


@router.get("/api/v1/buoys/{buoy_id}/battery/history", response_model=list[BatteryReading], tags=["battery"])
def battery_history(
    buoy_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    device_id: str | None = Query(default=None, pattern="^(A|B)$"),
    physical_device_id: str | None = Query(default=None, min_length=1, max_length=100),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> list[BatteryReading]:
    try:
        return list_battery_history(
            reader, buoy_id, limit, device_id, physical_device_id
        )
    except BatteryBuoyNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found"
        ) from None
    except BatteryDeviceNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from None


@router.get("/api/v1/buoys/{buoy_id}/battery-analysis", response_model=BatteryAnalysis, tags=["battery"])
def battery_analysis(
    buoy_id: str,
    device_id: str = Query(default="A", pattern="^(A|B)$"),
    window: int = Query(default=50, ge=1, le=500),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> BatteryAnalysis:
    result = analyze_if_buoy_exists(
        reader,
        buoy_id,
        lambda: analyze_battery_for_buoy(reader, buoy_id, device_id, window),
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found"
        )
    return BatteryAnalysis.model_validate(result, from_attributes=True)


@router.get("/api/v1/buoys/{buoy_id}/battery-health", response_model=BatteryHealth, tags=["battery"])
def battery_health(
    buoy_id: str,
    threshold: float = Query(default=10, gt=0, le=100),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
    metrics: BatteryMetrics = Depends(get_battery_metrics),
) -> BatteryHealth:
    result = evaluate_battery_health_for_buoy(reader, metrics, buoy_id, threshold)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found"
        )
    return BatteryHealth.model_validate(result, from_attributes=True)
