"""Read adapter composing IMU and location histories for wave analysis."""

from datetime import datetime

from sqlalchemy.orm import Session

from .buoy_location_repository import BuoyLocationRepository
from .domain.telemetry import ImuTelemetrySnapshot, LocationTelemetrySnapshot
from .imu_repository import ImuRepository


class WaveAnalysisRepository:
    """Provide wave-analysis inputs from their focused persistence adapters."""

    def __init__(self, db: Session) -> None:
        self.imu = ImuRepository(db)
        self.locations = BuoyLocationRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.locations.buoy_exists(buoy_id)

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        return self.imu.list_imu(buoy_id, limit, sensor_channel)

    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_locations(buoy_id, limit, since, until)
