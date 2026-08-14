from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .analytics import analyze_temperatures
from .models import (
    Buoy,
    BuoyCreate,
    BuoyStatusUpdate,
    BuoySummary,
    TemperatureReading,
    TemperatureReadingCreate,
    TemperatureAnalysis,
    TemperatureAlert,
    StoredTemperatureAlert,
)
from .repository import BuoyRepository
from .metrics import (
    buoy_last_seen_timestamp_seconds,
    current_temperature_celsius,
    temperature_readings_total,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Tidewatch API",
    description="API for monitoring autonomous ocean buoys.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/buoys", response_model=Buoy, status_code=status.HTTP_201_CREATED, tags=["buoys"])
def create_buoy(payload: BuoyCreate, db: Session = Depends(get_db)) -> Buoy:
    buoy = Buoy(
        id=f"TW-{uuid4().hex[:8].upper()}",
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        created_at=datetime.now(timezone.utc),
    )
    return BuoyRepository(db).create_buoy(buoy)


@app.get("/api/v1/buoys", response_model=list[BuoySummary], tags=["buoys"])
def list_buoys(db: Session = Depends(get_db)) -> list[BuoySummary]:
    repository = BuoyRepository(db)
    return [
        BuoySummary(buoy=buoy, latest_temperature=repository.latest_temperature(buoy.id))
        for buoy in repository.list_buoys()
    ]


@app.get("/api/v1/buoys/stale", response_model=list[BuoyHealth], tags=["buoys"])
def stale_buoys(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> list[BuoyHealth]:
    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    stale: list[BuoyHealth] = []

    for buoy in BuoyRepository(db).list_buoys():
        if buoy.status != "active" or buoy.last_seen_at is None:
            continue
        last_seen = buoy.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age_seconds = (now - last_seen).total_seconds()
        if age_seconds > max_age_seconds:
            stale.append(
                BuoyHealth(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    status=buoy.status,
                    last_seen_at=last_seen,
                    age_seconds=round(age_seconds, 2),
                    is_stale=True,
                )
            )

    return stale


@app.patch("/api/v1/buoys/{buoy_id}/status", response_model=Buoy, tags=["buoys"])
def update_buoy_status(
    buoy_id: str,
    payload: BuoyStatusUpdate,
    db: Session = Depends(get_db),
) -> Buoy:
    buoy = BuoyRepository(db).update_status(buoy_id, payload)
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return buoy


@app.post(
    "/api/v1/buoys/{buoy_id}/temperatures",
    response_model=TemperatureReading,
    status_code=status.HTTP_201_CREATED,
    tags=["temperature"],
)
def record_temperature(
    buoy_id: str,
    payload: TemperatureReadingCreate,
    db: Session = Depends(get_db),
) -> TemperatureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    reading = TemperatureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_temperature(reading)
    temperature_readings_total.labels(buoy_id=buoy_id).inc()
    current_temperature_celsius.labels(buoy_id=buoy_id).set(reading.temperature_celsius)
    buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(reading.measured_at.timestamp())
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/temperatures",
    response_model=list[TemperatureReading],
    tags=["temperature"],
)
def list_temperatures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TemperatureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_temperatures(buoy_id, limit)


@app.get(
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

    readings = [
        TemperatureReading.model_validate(reading)
        for reading in repository.list_temperatures(buoy_id, window)
    ]
    return analyze_temperatures(buoy_id, readings, threshold)


@app.get(
    "/api/v1/alerts/temperature",
    response_model=list[TemperatureAlert],
    tags=["alerts"],
)
def temperature_alerts(
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TemperatureAlert]:
    repository = BuoyRepository(db)
    alerts: list[TemperatureAlert] = []

    for buoy in repository.list_buoys():
        readings = [
            TemperatureReading.model_validate(reading)
            for reading in repository.list_temperatures(buoy.id, window)
        ]
        analysis = analyze_temperatures(buoy.id, readings, threshold)
        if analysis.is_anomaly and analysis.latest_temperature is not None:
            alerts.append(
                TemperatureAlert(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    severity="warning",
                    temperature_celsius=analysis.latest_temperature,
                    average_temperature=analysis.average_temperature or 0,
                    created_at=readings[0].measured_at,
                    message=analysis.anomaly_reason or "Temperature anomaly detected",
                )
            )

    return alerts


def stored_alert_response(alert) -> StoredTemperatureAlert:
    return StoredTemperatureAlert(
        id=alert.id,
        buoy_id=alert.buoy_id,
        buoy_name=alert.buoy.name,
        severity=alert.severity,
        temperature_celsius=alert.temperature_celsius,
        average_temperature=alert.average_temperature,
        created_at=alert.created_at,
        message=alert.message,
        status=alert.status,
        resolved_at=alert.resolved_at,
    )


@app.post(
    "/api/v1/alerts/temperature/evaluate",
    response_model=list[StoredTemperatureAlert],
    tags=["alerts"],
)
def evaluate_temperature_alerts(
    threshold: float = Query(default=2.0, gt=0, le=20),
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[StoredTemperatureAlert]:
    repository = BuoyRepository(db)
    stored_alerts = []

    for buoy in repository.list_buoys():
        readings = [
            TemperatureReading.model_validate(reading)
            for reading in repository.list_temperatures(buoy.id, window)
        ]
        analysis = analyze_temperatures(buoy.id, readings, threshold)
        if not analysis.is_anomaly or not readings:
            continue

        current_reading = readings[0]
        existing = repository.find_alert(buoy.id, current_reading.measured_at)
        if existing is None:
            alert = TemperatureAlert(
                buoy_id=buoy.id,
                buoy_name=buoy.name,
                severity="warning",
                temperature_celsius=analysis.latest_temperature or 0,
                average_temperature=analysis.average_temperature or 0,
                created_at=current_reading.measured_at,
                message=analysis.anomaly_reason or "Temperature anomaly detected",
            )
            existing = repository.create_alert(alert, current_reading.measured_at)
        stored_alerts.append(stored_alert_response(existing))

    return stored_alerts


@app.get(
    "/api/v1/alerts/temperature/stored",
    response_model=list[StoredTemperatureAlert],
    tags=["alerts"],
)
def stored_temperature_alerts(
    status_filter: str = Query(default="open", alias="status", pattern="^(open|resolved)$"),
    db: Session = Depends(get_db),
) -> list[StoredTemperatureAlert]:
    return [stored_alert_response(alert) for alert in BuoyRepository(db).list_alerts(status_filter)]


@app.post(
    "/api/v1/alerts/temperature/{alert_id}/resolve",
    response_model=StoredTemperatureAlert,
    tags=["alerts"],
)
def resolve_temperature_alert(alert_id: int, db: Session = Depends(get_db)) -> StoredTemperatureAlert:
    alert = BuoyRepository(db).resolve_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return stored_alert_response(alert)
