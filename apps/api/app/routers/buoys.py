"""HTTP routes for core buoy operations."""

from datetime import datetime, timezone
from csv import DictWriter
from io import StringIO
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..application.movement_analysis import analyze_movement_for_buoy
from ..database import get_db
from ..domain.staleness import stale_age_seconds
from ..metrics import buoy_movement_speed_mps
from ..models import (
    Buoy,
    BuoyCreate,
    BuoyHealth,
    BuoyLocationReading,
    BuoyLocationUpdate,
    BuoyStatusUpdate,
    BuoySummary,
)
from ..repository import BuoyRepository


router = APIRouter()


@router.post("/api/v1/buoys", response_model=Buoy, status_code=status.HTTP_201_CREATED, tags=["buoys"])
def create_buoy(payload: BuoyCreate, db: Session = Depends(get_db)) -> Buoy:
    buoy = Buoy(
        id=f"TW-{uuid4().hex[:8].upper()}",
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        created_at=datetime.now(timezone.utc),
    )
    return BuoyRepository(db).create_buoy(buoy)


@router.patch("/api/v1/buoys/{buoy_id}/status", response_model=Buoy, tags=["buoys"])
def update_buoy_status(
    buoy_id: str,
    payload: BuoyStatusUpdate,
    db: Session = Depends(get_db),
) -> Buoy:
    buoy = BuoyRepository(db).update_status(buoy_id, payload)
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return buoy


@router.patch("/api/v1/buoys/{buoy_id}/location", response_model=Buoy, tags=["buoys"])
def update_buoy_location(
    buoy_id: str,
    payload: BuoyLocationUpdate,
    db: Session = Depends(get_db),
) -> Buoy:
    buoy = BuoyRepository(db).update_location(buoy_id, payload)
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    repository = BuoyRepository(db)
    movement = analyze_movement_for_buoy(repository, buoy_id, 50)
    if movement.average_speed_mps is not None:
        buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(movement.average_speed_mps)
    return buoy


@router.get("/api/v1/buoys/stale", response_model=list[BuoyHealth], tags=["buoys"])
def stale_buoys(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> list[BuoyHealth]:
    now = datetime.now(timezone.utc)
    max_age_seconds = max_age_minutes * 60
    stale: list[BuoyHealth] = []
    for buoy in BuoyRepository(db).list_buoys():
        last_seen = buoy.last_seen_at
        age_seconds = stale_age_seconds(buoy.status, last_seen, max_age_seconds, now)
        if age_seconds is None or last_seen is None:
            continue
        normalized_last_seen = (
            last_seen.replace(tzinfo=timezone.utc)
            if last_seen.tzinfo is None
            else last_seen
        )
        stale.append(
            BuoyHealth(
                buoy_id=buoy.id,
                buoy_name=buoy.name,
                status=buoy.status,
                last_seen_at=normalized_last_seen,
                age_seconds=round(age_seconds, 2),
                is_stale=True,
            )
        )
    return stale


@router.get("/api/v1/buoys", response_model=list[BuoySummary], tags=["buoys"])
def list_buoys(db: Session = Depends(get_db)) -> list[BuoySummary]:
    repository = BuoyRepository(db)
    return [
        BuoySummary(
            buoy=buoy,
            latest_temperature=repository.latest_temperature(buoy.id),
            latest_temperature_a=repository.latest_temperature(buoy.id, "A"),
            latest_temperature_b=repository.latest_temperature(buoy.id, "B"),
            latest_pressure=repository.latest_pressure(buoy.id),
            latest_pressure_a=repository.latest_pressure(buoy.id, "A"),
            latest_pressure_b=repository.latest_pressure(buoy.id, "B"),
            latest_salinity=repository.latest_salinity(buoy.id),
            latest_salinity_a=repository.latest_salinity(buoy.id, "A"),
            latest_salinity_b=repository.latest_salinity(buoy.id, "B"),
            latest_imu=repository.latest_imu(buoy.id),
            latest_imu_a=repository.latest_imu(buoy.id, "A"),
            latest_imu_b=repository.latest_imu(buoy.id, "B"),
            latest_ambient_light=repository.latest_ambient_light(buoy.id),
            latest_ambient_light_a=repository.latest_ambient_light(buoy.id, "A"),
            latest_ambient_light_b=repository.latest_ambient_light(buoy.id, "B"),
            latest_wind=repository.latest_wind(buoy.id),
            latest_wind_a=repository.latest_wind(buoy.id, "A"),
            latest_wind_b=repository.latest_wind(buoy.id, "B"),
            latest_marine_current=repository.latest_marine_current(buoy.id),
            latest_marine_current_a=repository.latest_marine_current(buoy.id, "A"),
            latest_marine_current_b=repository.latest_marine_current(buoy.id, "B"),
            latest_turbidity=repository.latest_turbidity(buoy.id),
            latest_turbidity_a=repository.latest_turbidity(buoy.id, "A"),
            latest_turbidity_b=repository.latest_turbidity(buoy.id, "B"),
            latest_dissolved_oxygen=repository.latest_dissolved_oxygen(buoy.id),
            latest_dissolved_oxygen_a=repository.latest_dissolved_oxygen(buoy.id, "A"),
            latest_dissolved_oxygen_b=repository.latest_dissolved_oxygen(buoy.id, "B"),
            latest_ph=repository.latest_ph(buoy.id),
            latest_ph_a=repository.latest_ph(buoy.id, "A"),
            latest_ph_b=repository.latest_ph(buoy.id, "B"),
            latest_conductivity=repository.latest_conductivity(buoy.id),
            latest_conductivity_a=repository.latest_conductivity(buoy.id, "A"),
            latest_conductivity_b=repository.latest_conductivity(buoy.id, "B"),
            latest_chlorophyll_a=repository.latest_chlorophyll_a(buoy.id),
            latest_chlorophyll_a_a=repository.latest_chlorophyll_a(buoy.id, "A"),
            latest_chlorophyll_a_b=repository.latest_chlorophyll_a(buoy.id, "B"),
            latest_rainfall=repository.latest_rainfall(buoy.id),
            latest_rainfall_a=repository.latest_rainfall(buoy.id, "A"),
            latest_rainfall_b=repository.latest_rainfall(buoy.id, "B"),
            latest_humidity=repository.latest_humidity(buoy.id),
            latest_humidity_a=repository.latest_humidity(buoy.id, "A"),
            latest_humidity_b=repository.latest_humidity(buoy.id, "B"),
            latest_air_temperature=repository.latest_air_temperature(buoy.id),
            latest_air_temperature_a=repository.latest_air_temperature(buoy.id, "A"),
            latest_air_temperature_b=repository.latest_air_temperature(buoy.id, "B"),
            latest_atmospheric_pressure=repository.latest_atmospheric_pressure(buoy.id),
            latest_atmospheric_pressure_a=repository.latest_atmospheric_pressure(buoy.id, "A"),
            latest_atmospheric_pressure_b=repository.latest_atmospheric_pressure(buoy.id, "B"),
            latest_battery=repository.latest_battery(buoy.id),
            latest_battery_a=repository.latest_battery(buoy.id, "A"),
            latest_battery_b=repository.latest_battery(buoy.id, "B"),
        )
        for buoy in repository.list_buoys()
    ]


@router.get(
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


@router.get(
    "/api/v1/buoys/{buoy_id}/locations/export",
    response_class=Response,
    tags=["buoys"],
)
def export_buoy_locations(
    buoy_id: str,
    limit: int = Query(default=500, ge=1, le=5000),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> Response:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )
    output = StringIO()
    writer = DictWriter(output, fieldnames=["buoy_id", "latitude", "longitude", "measured_at"])
    writer.writeheader()
    for location in repository.list_locations(buoy_id, limit, since, until):
        writer.writerow(
            {
                "buoy_id": location.buoy_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "measured_at": location.measured_at.isoformat(),
            }
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{buoy_id}-locations.csv"'},
    )
