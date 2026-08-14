from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .analytics import analyze_temperatures
from .models import (
    Buoy,
    BuoyCreate,
    BuoySummary,
    TemperatureReading,
    TemperatureReadingCreate,
    TemperatureAnalysis,
)
from .repository import BuoyRepository


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


@app.post("/api/v1/buoys", response_model=Buoy, status_code=status.HTTP_201_CREATED, tags=["buoys"])
def create_buoy(payload: BuoyCreate, db: Session = Depends(get_db)) -> Buoy:
    buoy = Buoy(
        id=f"TW-{uuid4().hex[:8].upper()}",
        name=payload.name,
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
    return repository.add_temperature(reading)


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
