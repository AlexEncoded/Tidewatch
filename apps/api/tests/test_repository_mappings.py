from datetime import datetime, timezone
from types import SimpleNamespace

from app.domain.buoy import BuoySnapshot
from app.repository import _buoy_snapshot


def test_buoy_entity_mapper_returns_domain_snapshot_without_losing_fields() -> None:
    created_at = datetime(2026, 10, 5, tzinfo=timezone.utc)
    last_seen_at = datetime(2026, 10, 4, tzinfo=timezone.utc)
    entity = SimpleNamespace(
        id="TW-123",
        name="North buoy",
        latitude=36.7,
        longitude=3.1,
        status="maintenance",
        last_seen_at=last_seen_at,
        created_at=created_at,
    )

    snapshot = _buoy_snapshot(entity)

    assert snapshot == BuoySnapshot(
        buoy_id="TW-123",
        name="North buoy",
        latitude=36.7,
        longitude=3.1,
        status="maintenance",
        last_seen_at=last_seen_at,
        created_at=created_at,
    )
