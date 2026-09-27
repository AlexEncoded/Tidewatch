from datetime import datetime, timezone

from app.application.buoy_status import update_buoy_status
from app.domain.buoy import BuoySnapshot, BuoyStatusCommand


class FakeBuoyStatusRegistry:
    def __init__(self, result):
        self.result = result
        self.command = None

    def update_buoy_status(self, buoy_id, command):
        self.buoy_id = buoy_id
        self.command = command
        return self.result


def test_buoy_status_use_case_forwards_command_to_registry():
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    updated = BuoySnapshot("TW-123", "Buoy", None, None, "maintenance", None, now)
    registry = FakeBuoyStatusRegistry(updated)
    command = BuoyStatusCommand("maintenance")

    result = update_buoy_status(registry, "TW-123", command)

    assert result is updated
    assert registry.buoy_id == "TW-123"
    assert registry.command == command


def test_buoy_status_use_case_preserves_missing_buoy_result():
    registry = FakeBuoyStatusRegistry(None)

    assert update_buoy_status(registry, "missing", BuoyStatusCommand("inactive")) is None
