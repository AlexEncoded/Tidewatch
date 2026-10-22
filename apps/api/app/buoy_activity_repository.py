"""SQLAlchemy adapter for fleet activity queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain.buoy import BuoyActivitySnapshot
from .fleet_entities import BuoyEntity


class BuoyActivityRepository:
    """Read the operational heartbeat fields used by stale-buoy evaluation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_buoy_activity(self) -> list[BuoyActivitySnapshot]:
        buoys = self.db.scalars(
            select(BuoyEntity).order_by(BuoyEntity.created_at)
        ).all()
        return [
            BuoyActivitySnapshot(
                buoy_id=buoy.id,
                name=buoy.name,
                status=buoy.status,
                last_seen_at=buoy.last_seen_at,
            )
            for buoy in buoys
        ]
