"""Persisted temperature alert endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..adapter_dependencies import get_temperature_alert_store
from ..application.ports import TemperatureAlertStore
from ..application.temperature_alerts import (
    evaluate_and_store_temperature_alerts,
    list_stored_temperature_alerts,
    resolve_stored_temperature_alert,
)
from ..models import StoredTemperatureAlert

router = APIRouter()


@router.post("/api/v1/alerts/temperature/evaluate", response_model=list[StoredTemperatureAlert], tags=["alerts"])
def evaluate_temperature_alerts(
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    store: TemperatureAlertStore = Depends(get_temperature_alert_store),
) -> list[StoredTemperatureAlert]:
    return [
        StoredTemperatureAlert.model_validate(alert, from_attributes=True)
        for alert in evaluate_and_store_temperature_alerts(store, threshold, window)
    ]


@router.get("/api/v1/alerts/temperature/stored", response_model=list[StoredTemperatureAlert], tags=["alerts"])
def stored_temperature_alerts(
    status_filter: str = Query(default="open", alias="status", pattern="^(open|resolved)$"),
    store: TemperatureAlertStore = Depends(get_temperature_alert_store),
) -> list[StoredTemperatureAlert]:
    return [
        StoredTemperatureAlert.model_validate(alert, from_attributes=True)
        for alert in list_stored_temperature_alerts(store, status_filter)
    ]


@router.post("/api/v1/alerts/temperature/{alert_id}/resolve", response_model=StoredTemperatureAlert, tags=["alerts"])
def resolve_temperature_alert(
    alert_id: int,
    store: TemperatureAlertStore = Depends(get_temperature_alert_store),
) -> StoredTemperatureAlert:
    alert = resolve_stored_temperature_alert(store, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return StoredTemperatureAlert.model_validate(
        alert, from_attributes=True
    )
