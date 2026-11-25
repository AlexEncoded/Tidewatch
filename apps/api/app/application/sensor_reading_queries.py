"""Application queries for channel-filtered sensor telemetry."""

from collections.abc import Callable
from typing import Protocol, TypeVar

from ..domain.fleet.devices import SensorChannel
from ..domain.sensors.sensor_telemetry import SensorTelemetrySnapshot


class SensorReadingReader(Protocol):
    """Shared buoy-existence contract for sensor-reading queries."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


ReadingT = TypeVar("ReadingT", bound=SensorTelemetrySnapshot)


def list_sensor_readings(
    reader: SensorReadingReader,
    list_readings: Callable[[str, int, SensorChannel | None], list[ReadingT]],
    buoy_id: str,
    limit: int,
    sensor_channel: SensorChannel | None,
) -> list[ReadingT] | None:
    """Validate buoy existence and query one telemetry family through its port."""
    if not reader.buoy_exists(buoy_id):
        return None
    return list_readings(buoy_id, limit, sensor_channel)
