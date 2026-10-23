"""Application ports for temperature-anomaly detection and alert storage."""

from datetime import datetime
from typing import Protocol

from ..domain.buoy import BuoyIdentitySnapshot
from ..domain.temperature import TemperatureTelemetrySnapshot
from ..domain.temperature_alert import (
    TemperatureAlertSnapshot,
    TemperatureAnomalySnapshot,
)


class TemperatureAlertsReader(Protocol):
    """Read temperature telemetry and buoy identities for anomaly analysis."""

    def list_temperatures(
        self,
        buoy_id: str,
        limit: int,
        sensor_channel: str | None = "A",
    ) -> list[TemperatureTelemetrySnapshot]:
        ...

    def list_buoy_identities(self) -> list[BuoyIdentitySnapshot]:
        ...


class TemperatureAlertStore(TemperatureAlertsReader, Protocol):
    """Persist and query alerts generated from temperature anomalies."""

    def find_alert(
        self, buoy_id: str, measured_at: datetime
    ) -> TemperatureAlertSnapshot | None:
        ...

    def create_alert(
        self,
        alert: TemperatureAnomalySnapshot,
        reading_measured_at: datetime,
    ) -> TemperatureAlertSnapshot:
        ...

    def list_alerts(self, status: str = "open") -> list[TemperatureAlertSnapshot]:
        ...

    def resolve_alert(self, alert_id: int) -> TemperatureAlertSnapshot | None:
        ...
