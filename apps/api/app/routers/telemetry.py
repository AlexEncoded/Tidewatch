"""HTTP routes for fleet-wide telemetry operations."""

from csv import DictWriter
from datetime import datetime
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from ..adapter_dependencies import get_fleet_location_reader
from ..application.fleet_locations import list_fleet_locations
from ..application.location_queries import InvalidLocationTimeRange
from ..application.fleet_ports import FleetLocationReader


router = APIRouter()


@router.get(
    "/api/v1/locations/export",
    response_class=Response,
    tags=["telemetry"],
)
def export_fleet_locations(
    limit: int = Query(default=5000, ge=1, le=50000),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    reader: FleetLocationReader = Depends(get_fleet_location_reader),
) -> Response:
    try:
        locations = list_fleet_locations(reader, limit, since, until)
    except InvalidLocationTimeRange as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
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
        headers={"Content-Disposition": 'attachment; filename="tidewatch-locations.csv"'},
    )
