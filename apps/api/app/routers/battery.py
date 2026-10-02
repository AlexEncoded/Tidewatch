"""Battery telemetry and health endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..application.battery_analysis import analyze_battery_for_buoy
from ..application.battery_health import analyze_battery_health_for_buoy
from ..application.telemetry_ingestion import build_battery_snapshot
from ..adapter_dependencies import get_battery_telemetry_reader
from ..application.ports import BatteryTelemetryReader
from ..metrics import battery_delta_percent, battery_device_percent, battery_percent
from ..schemas.battery import (
    BatteryAnalysis,
    BatteryHealth,
    BatteryReading,
    BatteryReadingCreate,
)

router = APIRouter()


def ensure_buoy_exists(reader: BatteryTelemetryReader, buoy_id: str) -> None:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")


@router.post("/api/v1/buoys/{buoy_id}/battery", response_model=BatteryReading, status_code=status.HTTP_201_CREATED, tags=["battery"])
def record_battery(
    buoy_id: str,
    payload: BatteryReadingCreate,
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> BatteryReading:
    ensure_buoy_exists(reader, buoy_id)
    battery = build_battery_snapshot(buoy_id, payload.model_dump())
    saved_battery = reader.add_battery(battery)
    battery_percent.labels(buoy_id=buoy_id).set(battery.battery_percent)
    return saved_battery


@router.get("/api/v1/buoys/{buoy_id}/battery", response_model=BatteryReading | None, tags=["battery"])
def latest_battery(
    buoy_id: str,
    device_id: str | None = Query(default=None, pattern="^(A|B)$"),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> BatteryReading | None:
    ensure_buoy_exists(reader, buoy_id)
    return reader.latest_battery(buoy_id, device_id)


@router.get("/api/v1/buoys/{buoy_id}/battery/history", response_model=list[BatteryReading], tags=["battery"])
def battery_history(
    buoy_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    device_id: str | None = Query(default=None, pattern="^(A|B)$"),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> list[BatteryReading]:
    ensure_buoy_exists(reader, buoy_id)
    return reader.list_batteries(buoy_id, limit, device_id)


@router.get("/api/v1/buoys/{buoy_id}/battery-analysis", response_model=BatteryAnalysis, tags=["battery"])
def battery_analysis(
    buoy_id: str,
    device_id: str = Query(default="A", pattern="^(A|B)$"),
    window: int = Query(default=50, ge=1, le=500),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> BatteryAnalysis:
    ensure_buoy_exists(reader, buoy_id)
    result = analyze_battery_for_buoy(reader, buoy_id, device_id, window)
    return BatteryAnalysis.model_validate(result, from_attributes=True)


@router.get("/api/v1/buoys/{buoy_id}/battery-health", response_model=BatteryHealth, tags=["battery"])
def battery_health(
    buoy_id: str,
    threshold: float = Query(default=10, gt=0, le=100),
    reader: BatteryTelemetryReader = Depends(get_battery_telemetry_reader),
) -> BatteryHealth:
    ensure_buoy_exists(reader, buoy_id)
    result = analyze_battery_health_for_buoy(reader, buoy_id, threshold)
    for device_id, percentage in (("A", result.device_a_percent), ("B", result.device_b_percent)):
        if percentage is not None:
            battery_device_percent.labels(buoy_id=buoy_id, device_id=device_id).set(percentage)
    if result.delta_percent is not None:
        battery_delta_percent.labels(buoy_id=buoy_id).set(result.delta_percent)
    return BatteryHealth.model_validate(result, from_attributes=True)
