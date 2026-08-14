from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .analytics import analyze_pressure, analyze_temperatures
from .models import (
    Buoy,
    BuoyCreate,
    BuoyHealth,
    BuoyStatusUpdate,
    BuoySummary,
    PressureReading,
    PressureReadingCreate,
    PressureAnalysis,
    SalinityReading,
    SalinityReadingCreate,
    SensorHealth,
    TemperatureReading,
    TemperatureReadingCreate,
    TemperatureAnalysis,
    TemperatureAlert,
    StoredTemperatureAlert,
)
from .repository import BuoyRepository
from .metrics import (
    buoy_last_seen_timestamp_seconds,
    current_pressure_kpa,
    current_salinity_psu,
    current_temperature_celsius,
    pressure_readings_total,
    salinity_readings_total,
    sensor_degraded,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
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
        BuoySummary(
            buoy=buoy,
            latest_temperature=repository.latest_temperature(buoy.id),
            latest_pressure=repository.latest_pressure(buoy.id),
            latest_salinity=repository.latest_salinity(buoy.id),
        )
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
    temperature_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_temperature_celsius.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.temperature_celsius)
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
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[TemperatureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_temperatures(buoy_id, limit, sensor_channel)


@app.post(
    "/api/v1/buoys/{buoy_id}/pressures",
    response_model=PressureReading,
    status_code=status.HTTP_201_CREATED,
    tags=["pressure"],
)
def record_pressure(
    buoy_id: str,
    payload: PressureReadingCreate,
    db: Session = Depends(get_db),
) -> PressureReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = PressureReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_pressure(reading)
    pressure_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_pressure_kpa.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.pressure_kpa)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/pressures",
    response_model=list[PressureReading],
    tags=["pressure"],
)
def list_pressures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[PressureReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_pressures(buoy_id, limit, sensor_channel)


@app.get(
    "/api/v1/buoys/{buoy_id}/pressure-analysis",
    response_model=PressureAnalysis,
    tags=["pressure"],
)
def pressure_analysis(
    buoy_id: str,
    window: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PressureAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    readings = [
        PressureReading.model_validate(reading)
        for reading in repository.list_pressures(buoy_id, window)
    ]
    return analyze_pressure(buoy_id, readings)


@app.post(
    "/api/v1/buoys/{buoy_id}/salinity",
    response_model=SalinityReading,
    status_code=status.HTTP_201_CREATED,
    tags=["salinity"],
)
def record_salinity(
    buoy_id: str,
    payload: SalinityReadingCreate,
    db: Session = Depends(get_db),
) -> SalinityReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    reading = SalinityReading(buoy_id=buoy_id, **payload.model_dump())
    saved_reading = repository.add_salinity(reading)
    salinity_readings_total.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).inc()
    current_salinity_psu.labels(
        buoy_id=buoy_id, sensor_channel=reading.sensor_channel
    ).set(reading.salinity_psu)
    return saved_reading


@app.get(
    "/api/v1/buoys/{buoy_id}/salinity",
    response_model=list[SalinityReading],
    tags=["salinity"],
)
def list_salinity(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    sensor_channel: str = Query(default="A", pattern="^(A|B)$"),
    db: Session = Depends(get_db),
) -> list[SalinityReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.list_salinity(buoy_id, limit, sensor_channel)


@app.get(
    "/api/v1/buoys/{buoy_id}/sensor-health",
    response_model=SensorHealth,
    tags=["sensors"],
)
def sensor_health(buoy_id: str, db: Session = Depends(get_db)) -> SensorHealth:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    temperature_a = repository.list_temperatures(buoy_id, 1, "A")
    temperature_b = repository.list_temperatures(buoy_id, 1, "B")
    pressure_a = repository.list_pressures(buoy_id, 1, "A")
    pressure_b = repository.list_pressures(buoy_id, 1, "B")
    salinity_a = repository.list_salinity(buoy_id, 1, "A")
    salinity_b = repository.list_salinity(buoy_id, 1, "B")

    deltas = {
        "temperature": (
            round(abs(temperature_a[0].temperature_celsius - temperature_b[0].temperature_celsius), 3)
            if temperature_a and temperature_b
            else None
        ),
        "pressure": (
            round(abs(pressure_a[0].pressure_kpa - pressure_b[0].pressure_kpa), 3)
            if pressure_a and pressure_b
            else None
        ),
        "salinity": (
            round(abs(salinity_a[0].salinity_psu - salinity_b[0].salinity_psu), 3)
            if salinity_a and salinity_b
            else None
        ),
    }
    available = [value for value in deltas.values() if value is not None]
    thresholds = {"temperature": 0.5, "pressure": 0.25, "salinity": 0.2}
    degraded_sensors = [
        sensor
        for sensor, value in deltas.items()
        if value is not None and value > thresholds[sensor]
    ]
    status_value = "insufficient_data"
    if available:
        status_value = "degraded" if degraded_sensors else "consistent"

    for sensor in thresholds:
        sensor_degraded.labels(buoy_id=buoy_id, sensor=sensor).set(
            1 if sensor in degraded_sensors else 0
        )

    return SensorHealth(
        buoy_id=buoy_id,
        status=status_value,
        temperature_delta_celsius=deltas["temperature"],
        pressure_delta_kpa=deltas["pressure"],
        salinity_delta_psu=deltas["salinity"],
        degraded_sensors=degraded_sensors,
        checked_at=datetime.now(timezone.utc),
    )


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
