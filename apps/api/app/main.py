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
from .analytics import analyze_movement, analyze_pressure, analyze_temperatures
from .models import (
    Buoy,
    BuoyCreate,
    BuoyHealth,
    BuoyLocationUpdate,
    BuoyLocationReading,
    BuoyStatusUpdate,
    BuoySummary,
    BatteryReading,
    BatteryReadingCreate,
    MaintenanceIssue,
    MovementAnalysis,
    PressureReading,
    PressureReadingCreate,
    PressureAnalysis,
    SalinityReading,
    SalinityReadingCreate,
    SensorHealth,
    QualitySummary,
    TemperatureReading,
    TemperatureReadingCreate,
    TemperatureAnalysis,
    TemperatureAlert,
    StoredTemperatureAlert,
    TelemetryBatchCreate,
    TelemetryIngestResponse,
)
from .repository import BuoyRepository
from .metrics import (
    battery_percent,
    buoy_movement_speed_mps,
    buoy_last_seen_timestamp_seconds,
    current_pressure_kpa,
    current_salinity_psu,
    current_temperature_celsius,
    pressure_readings_total,
    reading_quality_total,
    salinity_readings_total,
    sensor_degraded,
    temperature_readings_total,
)


def record_quality_metric(
    buoy_id: str, sensor_family: str, sensor_channel: str, quality: str
) -> None:
    reading_quality_total.labels(
        buoy_id=buoy_id,
        sensor_family=sensor_family,
        sensor_channel=sensor_channel,
        quality=quality,
    ).inc()


def latest_usable_reading(readings: list) -> list:
    return [reading for reading in readings if reading.quality != "invalid"][:1]


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


@app.post(
    "/api/v1/buoys/{buoy_id}/telemetry",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["telemetry"],
)
def ingest_telemetry(
    buoy_id: str,
    payload: TelemetryBatchCreate,
    db: Session = Depends(get_db),
) -> TelemetryIngestResponse:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    if payload.location is not None:
        repository.add_location(
            BuoyLocationReading(buoy_id=buoy_id, **payload.location.model_dump())
        )
        movement = analyze_movement(buoy_id, repository.list_locations(buoy_id, 50))
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(
                movement.average_speed_mps
            )

    accepted = 0
    accepted_by_family = {
        "temperature": 0,
        "pressure": 0,
        "salinity": 0,
        "battery": 0,
    }
    for reading_payload in payload.temperatures:
        reading = TemperatureReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_temperature(reading)
        temperature_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_temperature_celsius.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.temperature_celsius)
        record_quality_metric(buoy_id, "temperature", reading.sensor_channel, reading.quality)
        buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy_id).set(
            reading.measured_at.timestamp()
        )
        accepted_by_family["temperature"] += 1
        accepted += 1

    for reading_payload in payload.pressures:
        reading = PressureReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_pressure(reading)
        pressure_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_pressure_kpa.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.pressure_kpa)
        record_quality_metric(buoy_id, "pressure", reading.sensor_channel, reading.quality)
        accepted_by_family["pressure"] += 1
        accepted += 1

    for reading_payload in payload.salinity:
        reading = SalinityReading(buoy_id=buoy_id, **reading_payload.model_dump())
        repository.add_salinity(reading)
        salinity_readings_total.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        current_salinity_psu.labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.salinity_psu)
        record_quality_metric(buoy_id, "salinity", reading.sensor_channel, reading.quality)
        accepted_by_family["salinity"] += 1
        accepted += 1

    if payload.battery is not None:
        battery = BatteryReading(buoy_id=buoy_id, **payload.battery.model_dump())
        repository.add_battery(battery)
        battery_percent.labels(buoy_id=buoy_id).set(battery.battery_percent)
        accepted_by_family["battery"] += 1
        accepted += 1

    return TelemetryIngestResponse(
        buoy_id=buoy_id,
        accepted_readings=accepted,
        accepted_by_family=accepted_by_family,
    )


@app.get("/api/v1/buoys", response_model=list[BuoySummary], tags=["buoys"])
def list_buoys(db: Session = Depends(get_db)) -> list[BuoySummary]:
    repository = BuoyRepository(db)
    return [
        BuoySummary(
            buoy=buoy,
            latest_temperature=repository.latest_temperature(buoy.id),
            latest_pressure=repository.latest_pressure(buoy.id),
            latest_salinity=repository.latest_salinity(buoy.id),
            latest_battery=repository.latest_battery(buoy.id),
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


@app.patch("/api/v1/buoys/{buoy_id}/location", response_model=Buoy, tags=["buoys"])
def update_buoy_location(
    buoy_id: str,
    payload: BuoyLocationUpdate,
    db: Session = Depends(get_db),
) -> Buoy:
    buoy = BuoyRepository(db).update_location(buoy_id, payload)
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    movement = analyze_movement(buoy_id, BuoyRepository(db).list_locations(buoy_id, 50))
    if movement.average_speed_mps is not None:
        buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(movement.average_speed_mps)
    return buoy


@app.get(
    "/api/v1/buoys/{buoy_id}/locations",
    response_model=list[BuoyLocationReading],
    tags=["buoys"],
)
def list_buoy_locations(
    buoy_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[BuoyLocationReading]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )
    return repository.list_locations(buoy_id, limit, since, until)


@app.get(
    "/api/v1/buoys/{buoy_id}/movement-analysis",
    response_model=MovementAnalysis,
    tags=["buoys"],
)
def buoy_movement_analysis(
    buoy_id: str,
    window: int = Query(default=100, ge=2, le=500),
    db: Session = Depends(get_db),
) -> MovementAnalysis:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return analyze_movement(buoy_id, repository.list_locations(buoy_id, window))


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
    record_quality_metric(buoy_id, "temperature", reading.sensor_channel, reading.quality)
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
    record_quality_metric(buoy_id, "pressure", reading.sensor_channel, reading.quality)
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
        if reading.quality != "invalid"
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
    record_quality_metric(buoy_id, "salinity", reading.sensor_channel, reading.quality)
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


@app.post(
    "/api/v1/buoys/{buoy_id}/battery",
    response_model=BatteryReading,
    status_code=status.HTTP_201_CREATED,
    tags=["battery"],
)
def record_battery(
    buoy_id: str,
    payload: BatteryReadingCreate,
    db: Session = Depends(get_db),
) -> BatteryReading:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    battery = BatteryReading(buoy_id=buoy_id, **payload.model_dump())
    saved_battery = repository.add_battery(battery)
    battery_percent.labels(buoy_id=buoy_id).set(battery.battery_percent)
    return saved_battery


@app.get(
    "/api/v1/buoys/{buoy_id}/battery",
    response_model=BatteryReading | None,
    tags=["battery"],
)
def latest_battery(buoy_id: str, db: Session = Depends(get_db)) -> BatteryReading | None:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return repository.latest_battery(buoy_id)


@app.get(
    "/api/v1/buoys/{buoy_id}/quality-summary",
    response_model=QualitySummary,
    tags=["quality"],
)
def quality_summary(buoy_id: str, db: Session = Depends(get_db)) -> QualitySummary:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    counts = repository.quality_counts(buoy_id)
    return QualitySummary(
        buoy_id=buoy_id,
        total_readings=sum(counts.values()),
        good_readings=counts["good"],
        suspect_readings=counts["suspect"],
        invalid_readings=counts["invalid"],
    )


@app.get(
    "/api/v1/buoys/{buoy_id}/sensor-health",
    response_model=SensorHealth,
    tags=["sensors"],
)
def sensor_health(buoy_id: str, db: Session = Depends(get_db)) -> SensorHealth:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    temperature_a = latest_usable_reading(repository.list_temperatures(buoy_id, 50, "A"))
    temperature_b = latest_usable_reading(repository.list_temperatures(buoy_id, 50, "B"))
    pressure_a = latest_usable_reading(repository.list_pressures(buoy_id, 50, "A"))
    pressure_b = latest_usable_reading(repository.list_pressures(buoy_id, 50, "B"))
    salinity_a = latest_usable_reading(repository.list_salinity(buoy_id, 50, "A"))
    salinity_b = latest_usable_reading(repository.list_salinity(buoy_id, 50, "B"))

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
    "/api/v1/maintenance/issues",
    response_model=list[MaintenanceIssue],
    tags=["maintenance"],
)
def maintenance_issues(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    drift_speed_mps: float = Query(default=1.0, gt=0, le=100),
    db: Session = Depends(get_db),
) -> list[MaintenanceIssue]:
    repository = BuoyRepository(db)
    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    issues: list[MaintenanceIssue] = []

    for buoy in repository.list_buoys():
        if buoy.status == "active" and buoy.last_seen_at is not None:
            last_seen = buoy.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if (now - last_seen).total_seconds() > max_age_seconds:
                issues.append(
                    MaintenanceIssue(
                        buoy_id=buoy.id,
                        buoy_name=buoy.name,
                        issue_type="silent_buoy",
                        severity="warning",
                        message=f"No telemetry received for more than {max_age_minutes:g} minutes",
                    )
                )

        health = sensor_health(buoy.id, db)
        if health.status == "degraded":
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="degraded_sensor",
                    severity="warning",
                    message=f"Degraded sensors: {', '.join(health.degraded_sensors)}",
                )
            )

        latest_readings = {
            "temperature": repository.list_temperatures(buoy.id, 1),
            "pressure": repository.list_pressures(buoy.id, 1),
            "salinity": repository.list_salinity(buoy.id, 1),
        }
        invalid_sensors = [
            sensor
            for sensor, readings in latest_readings.items()
            if readings and readings[0].quality == "invalid"
        ]
        if invalid_sensors:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="invalid_reading",
                    severity="warning",
                    message=f"Invalid latest readings: {', '.join(invalid_sensors)}",
                )
            )

        suspect_sensors = [
            sensor
            for sensor, readings in latest_readings.items()
            if readings and readings[0].quality == "suspect"
        ]
        if suspect_sensors:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="suspect_reading",
                    severity="warning",
                    message=f"Suspect latest readings: {', '.join(suspect_sensors)}",
                )
            )

        battery = repository.latest_battery(buoy.id)
        if battery is not None and battery.battery_percent < 20:
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="low_battery",
                    severity="critical" if battery.battery_percent < 10 else "warning",
                    message=f"Battery level is {battery.battery_percent:.1f}%",
                )
            )

        movement = analyze_movement(buoy.id, repository.list_locations(buoy.id, 50))
        if movement.average_speed_mps is not None:
            buoy_movement_speed_mps.labels(buoy_id=buoy.id).set(movement.average_speed_mps)
        if (
            movement.average_speed_mps is not None
            and movement.average_speed_mps > drift_speed_mps
        ):
            issues.append(
                MaintenanceIssue(
                    buoy_id=buoy.id,
                    buoy_name=buoy.name,
                    issue_type="drift_detected",
                    severity="warning",
                    message=(
                        f"Average movement speed is {movement.average_speed_mps:.3f} m/s, "
                        f"above the configured limit of {drift_speed_mps:g} m/s"
                    ),
                )
            )

    return issues


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
        if reading.quality != "invalid"
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
            if reading.quality != "invalid"
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
            if reading.quality != "invalid"
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
