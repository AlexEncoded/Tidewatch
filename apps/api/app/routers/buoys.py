"""HTTP routes for core buoy operations."""

from datetime import datetime, timezone
from csv import DictWriter
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from ..application.buoy_location_update import update_buoy_location as record_buoy_location
from ..application.buoy_registration import register_buoy as create_buoy_use_case
from ..application.buoy_locations import list_buoy_locations as query_buoy_locations
from ..adapter_dependencies import get_buoy_location_history_reader
from ..adapter_dependencies import get_buoy_summary_reader
from ..application.ports import BuoyLocationHistoryReader, BuoyLocationUpdater
from ..application.ports import BuoySummaryReader
from ..application.ports import StaleBuoyReader, BuoyStatusRegistry
from ..application.buoy_status import update_buoy_status as change_buoy_status
from ..adapter_dependencies import get_buoy_status_registry
from ..adapter_dependencies import (
    get_buoy_location_updater,
    get_buoy_registrar,
    get_movement_analysis_reader,
)
from ..application.ports import MovementAnalysisReader, BuoyRegistrar
from ..domain.buoy import BuoyLocationCommand, BuoyRegistrationCommand, BuoyStatusCommand
from ..application.stale_buoys import find_stale_buoys
from ..adapter_dependencies import get_stale_buoy_reader
from ..metrics import buoy_last_seen_timestamp_seconds, buoy_movement_speed_mps
from ..schemas.fleet_summary import BuoySummary
from ..schemas.fleet import (
    Buoy,
    BuoyCreate,
    BuoyHealth,
    BuoyLocationReading,
    BuoyLocationUpdate,
    BuoyStatusUpdate,
)


router = APIRouter()


@router.post("/api/v1/buoys", response_model=Buoy, status_code=status.HTTP_201_CREATED, tags=["buoys"])
def create_buoy(
    payload: BuoyCreate,
    registrar: BuoyRegistrar = Depends(get_buoy_registrar),
) -> Buoy:
    buoy = create_buoy_use_case(
        registrar,
        BuoyRegistrationCommand(
            name=payload.name,
            latitude=payload.latitude,
            longitude=payload.longitude,
        ),
    )
    buoy_last_seen_timestamp_seconds.labels(buoy_id=buoy.buoy_id).set(
        buoy.last_seen_at.timestamp() if buoy.last_seen_at is not None else 0
    )
    return Buoy(
        id=buoy.buoy_id,
        name=buoy.name,
        latitude=buoy.latitude,
        longitude=buoy.longitude,
        status=buoy.status,
        last_seen_at=buoy.last_seen_at,
        created_at=buoy.created_at,
    )


@router.patch("/api/v1/buoys/{buoy_id}/status", response_model=Buoy, tags=["buoys"])
def update_buoy_status(
    buoy_id: str,
    payload: BuoyStatusUpdate,
    registry: BuoyStatusRegistry = Depends(get_buoy_status_registry),
) -> Buoy:
    buoy = change_buoy_status(
        registry, buoy_id, BuoyStatusCommand(status=payload.status)
    )
    if buoy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return Buoy(
        id=buoy.buoy_id,
        name=buoy.name,
        latitude=buoy.latitude,
        longitude=buoy.longitude,
        status=buoy.status,
        last_seen_at=buoy.last_seen_at,
        created_at=buoy.created_at,
    )


@router.patch("/api/v1/buoys/{buoy_id}/location", response_model=Buoy, tags=["buoys"])
def update_buoy_location(
    buoy_id: str,
    payload: BuoyLocationUpdate,
    updater: BuoyLocationUpdater = Depends(get_buoy_location_updater),
    movement_reader: MovementAnalysisReader = Depends(get_movement_analysis_reader),
) -> Buoy:
    result = record_buoy_location(
        updater,
        movement_reader,
        buoy_id,
        BuoyLocationCommand(latitude=payload.latitude, longitude=payload.longitude),
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    if result.movement.average_speed_mps is not None:
        buoy_movement_speed_mps.labels(buoy_id=buoy_id).set(result.movement.average_speed_mps)
    buoy = result.buoy
    return Buoy(
        id=buoy.buoy_id,
        name=buoy.name,
        latitude=buoy.latitude,
        longitude=buoy.longitude,
        status=buoy.status,
        last_seen_at=buoy.last_seen_at,
        created_at=buoy.created_at,
    )


@router.get("/api/v1/buoys/stale", response_model=list[BuoyHealth], tags=["buoys"])
def stale_buoys(
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    reader: StaleBuoyReader = Depends(get_stale_buoy_reader),
) -> list[BuoyHealth]:
    return [
        BuoyHealth(
            buoy_id=buoy.buoy_id,
            buoy_name=buoy.name,
            status=buoy.status,
            last_seen_at=buoy.last_seen_at,
            age_seconds=buoy.age_seconds,
            is_stale=True,
        )
        for buoy in find_stale_buoys(reader, max_age_minutes * 60)
    ]


@router.get("/api/v1/buoys", response_model=list[BuoySummary], tags=["buoys"])
def list_buoys(
    reader: BuoySummaryReader = Depends(get_buoy_summary_reader),
) -> list[BuoySummary]:
    return [
        BuoySummary(
            buoy=Buoy(
                id=summary.buoy.buoy_id,
                name=summary.buoy.name,
                latitude=summary.buoy.latitude,
                longitude=summary.buoy.longitude,
                status=summary.buoy.status,
                last_seen_at=summary.buoy.last_seen_at,
                created_at=summary.buoy.created_at,
            ),
            **{
                field_name: reading
                for family, channels in summary.latest_readings.items()
                for field_name, reading in (
                    (f"latest_{family}", channels["latest"]),
                    (f"latest_{family}_a", channels["A"]),
                    (f"latest_{family}_b", channels["B"]),
                )
            }
        )
        for summary in reader.list_buoy_summaries()
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
    reader: BuoyLocationHistoryReader = Depends(get_buoy_location_history_reader),
) -> list[BuoyLocationReading]:
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )
    locations = query_buoy_locations(reader, buoy_id, limit, since, until)
    if locations is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return locations


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
    reader: BuoyLocationHistoryReader = Depends(get_buoy_location_history_reader),
) -> Response:
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )
    locations = query_buoy_locations(reader, buoy_id, limit, since, until)
    if locations is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    output = StringIO()
    writer = DictWriter(output, fieldnames=["buoy_id", "latitude", "longitude", "measured_at"])
    writer.writeheader()
    for location in locations:
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
