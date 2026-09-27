from datetime import datetime, timedelta, timezone

from app.application.stale_buoys import find_stale_buoys
from app.domain.buoy import BuoyActivitySnapshot


class FakeStaleBuoyReader:
    def __init__(self, readings):
        self.readings = readings

    def list_buoy_activity(self):
        return self.readings


def test_stale_buoy_query_returns_only_active_buoys_over_threshold():
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    reader = FakeStaleBuoyReader(
        [
            BuoyActivitySnapshot("old", "Old buoy", "active", now - timedelta(minutes=40)),
            BuoyActivitySnapshot("fresh", "Fresh buoy", "active", now - timedelta(minutes=5)),
            BuoyActivitySnapshot("maintenance", "Maintenance", "maintenance", now - timedelta(hours=2)),
            BuoyActivitySnapshot("never", "Never seen", "active", None),
        ]
    )

    stale = find_stale_buoys(reader, 30 * 60, now)

    assert [(buoy.buoy_id, buoy.age_seconds) for buoy in stale] == [("old", 2400.0)]


def test_stale_buoy_query_normalizes_naive_last_seen_timestamps():
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    reader = FakeStaleBuoyReader(
        [BuoyActivitySnapshot("old", "Old buoy", "active", (now - timedelta(minutes=1)).replace(tzinfo=None))]
    )

    stale = find_stale_buoys(reader, 30, now)

    assert stale[0].last_seen_at.tzinfo == timezone.utc
    assert stale[0].age_seconds == 60
