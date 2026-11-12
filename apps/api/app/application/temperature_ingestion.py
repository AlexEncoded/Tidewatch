"""Application use case for writing water-temperature telemetry."""

from datetime import datetime, timezone

from ..domain.temperature import TemperatureTelemetrySnapshot
from .marine_water_ports import TemperatureTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_temperature_reading(
    gateway: TemperatureTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: TemperatureTelemetrySnapshot,
    received_at: datetime | None = None,
) -> TemperatureTelemetrySnapshot | None:
    """Persist one water-temperature reading and publish its metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_temperature(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "temperature",
        reading.sensor_channel,
        reading.quality,
        {"temperature_celsius": reading.temperature_celsius},
    )
    return saved_reading
