from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, status

from .models import (
    Buoy,
    BuoyCreate,
    BuoySummary,
    TemperatureReading,
    TemperatureReadingCreate,
)
from .store import InMemoryStore, create_store

app = FastAPI(
    title="Tidewatch API",
    description="API for monitoring autonomous ocean buoys.",
    version="0.1.0",
)
store: InMemoryStore = create_store()


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/buoys", response_model=Buoy, status_code=status.HTTP_201_CREATED, tags=["buoys"])
def create_buoy(payload: BuoyCreate) -> Buoy:
    buoy = Buoy(
        id=f"TW-{uuid4().hex[:8].upper()}",
        name=payload.name,
        created_at=datetime.now(timezone.utc),
    )
    return store.add_buoy(buoy)


@app.get("/api/v1/buoys", response_model=list[BuoySummary], tags=["buoys"])
def list_buoys() -> list[BuoySummary]:
    return [
        BuoySummary(buoy=buoy, latest_temperature=store.get_latest_reading(buoy.id))
        for buoy in store.buoys.values()
    ]


@app.post(
    "/api/v1/buoys/{buoy_id}/temperatures",
    response_model=TemperatureReading,
    status_code=status.HTTP_201_CREATED,
    tags=["temperature"],
)
def record_temperature(buoy_id: str, payload: TemperatureReadingCreate) -> TemperatureReading:
    if store.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")

    reading = TemperatureReading(buoy_id=buoy_id, **payload.model_dump())
    return store.add_reading(reading)


@app.get(
    "/api/v1/buoys/{buoy_id}/temperatures",
    response_model=list[TemperatureReading],
    tags=["temperature"],
)
def list_temperatures(
    buoy_id: str,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[TemperatureReading]:
    if store.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return store.get_readings(buoy_id)[:limit]
