"""HTTP routes for fleet-wide telemetry operations."""

from csv import DictWriter
from datetime import datetime
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..repository import BuoyRepository


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
    db: Session = Depends(get_db),
) -> Response:
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="since must be earlier than or equal to until",
        )
    output = StringIO()
    writer = DictWriter(output, fieldnames=["buoy_id", "latitude", "longitude", "measured_at"])
    writer.writeheader()
    for location in BuoyRepository(db).list_all_locations(limit, since, until):
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
