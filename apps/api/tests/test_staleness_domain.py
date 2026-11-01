from datetime import datetime, timedelta, timezone

from app.domain.buoy import BuoyActivitySnapshot
from app.domain.staleness import classify_stale_buoy


def test_stale_buoy_classification_builds_snapshot_and_normalizes_naive_time() -> None:
    now = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    last_seen = now - timedelta(seconds=60)
    buoy = BuoyActivitySnapshot("TW-1", "North buoy", "active", last_seen.replace(tzinfo=None))

    stale = classify_stale_buoy(buoy, 30, now)

    assert stale is not None
    assert stale.buoy_id == "TW-1"
    assert stale.last_seen_at == last_seen
    assert stale.last_seen_at.tzinfo == timezone.utc
    assert stale.age_seconds == 60


def test_stale_buoy_classification_returns_none_when_not_stale() -> None:
    now = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    buoy = BuoyActivitySnapshot("TW-1", "North buoy", "active", now)

    assert classify_stale_buoy(buoy, 30, now) is None
