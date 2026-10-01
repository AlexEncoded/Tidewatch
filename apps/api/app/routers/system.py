"""HTTP routes for system health and observability endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ..adapter_dependencies import get_database_health_reader
from ..application.ports import DatabaseHealthReader


router = APIRouter()


@router.get("/health", tags=["system"])
def health(
    reader: DatabaseHealthReader = Depends(get_database_health_reader),
) -> dict[str, str]:
    reader.check_database()
    return {"status": "ok"}


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
