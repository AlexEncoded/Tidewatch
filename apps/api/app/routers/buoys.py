"""HTTP routes for core buoy operations."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..application.movement_analysis import analyze_movement_for_buoy
from ..database import get_db
from ..domain.staleness import stale_age_seconds
from ..metrics import buoy_movement_speed_mps
from ..models import Buoy, BuoyCreate, BuoyHealth, BuoyLocationUpdate, BuoyStatusUpdate
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
