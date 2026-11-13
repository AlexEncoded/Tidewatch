"""Application use case for writing air-temperature telemetry."""

from datetime import datetime, timezone

from ..domain.air_temperature import AirTemperatureTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .weather_ports import AirTemperatureTelemetryGateway


def ingest_air_temperature_reading(
    gateway: AirTemperatureTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: AirTemperatureTelemetrySnapshot,
    received_at: datetime | None = None,
) -> AirTemperatureTelemetrySnapshot | None:
    """Persist one air-temperature reading and publish its metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_air_temperature(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "air_temperature",
        reading.sensor_channel,
        reading.quality,
        {"air_temperature_celsius": reading.air_temperature_celsius},
    )
    return saved_reading
