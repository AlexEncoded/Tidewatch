"""Persisted temperature alert endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.temperature_analysis import analyze_temperature_readings, list_valid_temperature_readings
from ..database import get_db
from ..models import StoredTemperatureAlert, TemperatureAlert
from ..repository import BuoyRepository

router = APIRouter()


def stored_alert_response(alert) -> StoredTemperatureAlert:
    return StoredTemperatureAlert(
        id=alert.id, buoy_id=alert.buoy_id, buoy_name=alert.buoy.name,
        severity=alert.severity, temperature_celsius=alert.temperature_celsius,
        average_temperature=alert.average_temperature, created_at=alert.created_at,
        message=alert.message, status=alert.status, resolved_at=alert.resolved_at,
    )


@router.post("/api/v1/alerts/temperature/evaluate", response_model=list[StoredTemperatureAlert], tags=["alerts"])
def evaluate_temperature_alerts(threshold: float = Query(default=2.0, gt=0, le=20), window: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> list[StoredTemperatureAlert]:
    repository = BuoyRepository(db)
    stored_alerts = []
    for buoy in repository.list_buoys():
        readings = list_valid_temperature_readings(repository, buoy.id, window)
        analysis = analyze_temperature_readings(buoy.id, readings, threshold)
        if not analysis.is_anomaly or not readings:
            continue
        current_reading = readings[0]
        existing = repository.find_alert(buoy.id, current_reading.measured_at)
        if existing is None:
            existing = repository.create_alert(
                TemperatureAlert(
                    buoy_id=buoy.id, buoy_name=buoy.name, severity="warning",
                    temperature_celsius=analysis.latest_temperature or 0,
                    average_temperature=analysis.average_temperature or 0,
                    created_at=current_reading.measured_at,
                    message=analysis.anomaly_reason or "Temperature anomaly detected",
                ),
                current_reading.measured_at,
            )
        stored_alerts.append(stored_alert_response(existing))
    return stored_alerts


@router.get("/api/v1/alerts/temperature/stored", response_model=list[StoredTemperatureAlert], tags=["alerts"])
def stored_temperature_alerts(status_filter: str = Query(default="open", alias="status", pattern="^(open|resolved)$"), db: Session = Depends(get_db)) -> list[StoredTemperatureAlert]:
    return [stored_alert_response(alert) for alert in BuoyRepository(db).list_alerts(status_filter)]


@router.post("/api/v1/alerts/temperature/{alert_id}/resolve", response_model=StoredTemperatureAlert, tags=["alerts"])
def resolve_temperature_alert(alert_id: int, db: Session = Depends(get_db)) -> StoredTemperatureAlert:
    alert = BuoyRepository(db).resolve_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return stored_alert_response(alert)
