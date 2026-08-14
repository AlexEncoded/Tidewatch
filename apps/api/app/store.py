from datetime import datetime, timezone

from .models import Buoy, TemperatureReading


class InMemoryStore:
    """Temporary repository used by the first MVP iteration."""

    def __init__(self) -> None:
        self.buoys: dict[str, Buoy] = {}
        self.readings: dict[str, list[TemperatureReading]] = {}

    def add_buoy(self, buoy: Buoy) -> Buoy:
        self.buoys[buoy.id] = buoy
        self.readings[buoy.id] = []
        return buoy

    def get_buoy(self, buoy_id: str) -> Buoy | None:
        return self.buoys.get(buoy_id)

    def add_reading(self, reading: TemperatureReading) -> TemperatureReading:
        self.readings[reading.buoy_id].append(reading)
        return reading

    def get_readings(self, buoy_id: str) -> list[TemperatureReading]:
        return sorted(
            self.readings[buoy_id], key=lambda reading: reading.measured_at, reverse=True
        )

    def get_latest_reading(self, buoy_id: str) -> TemperatureReading | None:
        readings = self.get_readings(buoy_id)
        return readings[0] if readings else None


def create_store() -> InMemoryStore:
    store = InMemoryStore()
    store.add_buoy(
        Buoy(
            id="TW-001",
            name="North Atlantic Sentinel",
            created_at=datetime.now(timezone.utc),
        )
    )
    return store
