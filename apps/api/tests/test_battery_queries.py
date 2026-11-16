from types import SimpleNamespace

import pytest

from app.application.battery_queries import (
    get_latest_battery,
    list_battery_history,
)
from app.application.battery_errors import BatteryBuoyNotFound, BatteryDeviceNotFound


@pytest.mark.parametrize("query", [get_latest_battery, list_battery_history])
def test_battery_queries_validate_buoy_before_reading(query) -> None:
    calls = []

    class Reader:
        def buoy_exists(self, buoy_id):
            calls.append(("exists", buoy_id))
            return False

        def latest_battery(self, *args):
            raise AssertionError("missing buoy must not query a reading")

        def list_batteries(self, *args):
            raise AssertionError("missing buoy must not query history")

    with pytest.raises(BatteryBuoyNotFound):
        if query is get_latest_battery:
            query(Reader(), "missing", None, None)
        else:
            query(Reader(), "missing", 20, None, None)

    assert calls == [("exists", "missing")]


def test_latest_battery_query_checks_physical_device_ownership() -> None:
    class Reader:
        def buoy_exists(self, buoy_id):
            return True

        def get_device_snapshot(self, device_id):
            return SimpleNamespace(buoy_id="other-buoy")

        def latest_battery(self, *args):
            raise AssertionError("foreign device must not query a reading")

    with pytest.raises(BatteryDeviceNotFound, match="Device not found"):
        get_latest_battery(Reader(), "buoy-1", None, "device-1")


def test_battery_history_query_forwards_filters_after_validation() -> None:
    expected = [SimpleNamespace(battery_percent=81.0)]

    class Reader:
        def buoy_exists(self, buoy_id):
            return True

        def get_device_snapshot(self, device_id):
            return SimpleNamespace(buoy_id="buoy-1")

        def list_batteries(self, *args):
            assert args == ("buoy-1", 12, "B", "device-1")
            return expected

    assert list_battery_history(Reader(), "buoy-1", 12, "B", "device-1") == expected
