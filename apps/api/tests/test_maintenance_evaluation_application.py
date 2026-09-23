from datetime import datetime, timezone
from types import SimpleNamespace

from app.application.maintenance_evaluation import (
    evaluate_maintenance_buoy,
    evaluate_maintenance_fleet,
)


def test_maintenance_evaluation_coordinates_application_services() -> None:
    class Reader:
        def latest_battery(self, buoy_id: str, device_id: str):
            return None

        def list_locations(self, buoy_id: str, limit: int):
            return []

        def list_devices(self, buoy_id: str):
            return []

        def __getattr__(self, name):
            if name.startswith("list_"):
                return lambda buoy_id, limit, channel=None: []
            raise AttributeError(name)

    now = datetime.now(timezone.utc)
    buoy = SimpleNamespace(
        id="buoy-1",
        name="North buoy",
        status="active",
        last_seen_at=now,
    )

    result = evaluate_maintenance_buoy(Reader(), buoy, now, 30, 1)

    assert result.issues == []
    assert result.battery_health.status == "insufficient_data"
    assert result.average_speed_mps is None


def test_maintenance_fleet_evaluation_reads_buoys_through_the_port() -> None:
    class Reader:
        def list_buoys(self):
            return []

    evaluations = evaluate_maintenance_fleet(
        Reader(), datetime.now(timezone.utc), 30, 1
    )

    assert evaluations == []
