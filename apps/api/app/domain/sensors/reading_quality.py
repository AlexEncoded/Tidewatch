from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Protocol, TypeVar

from ..shared.reading_quality import ReadingQuality, VALID_READING_QUALITIES


class MeasuredReading(Protocol):
    quality: ReadingQuality
    measured_at: datetime


ReadingT = TypeVar("ReadingT", bound=MeasuredReading)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def latest_usable_reading(
    readings: Sequence[ReadingT],
    max_age_seconds: float | None = None,
    now: datetime | None = None,
) -> list[ReadingT]:
    """Return the newest non-invalid reading within the optional age window."""
    reference_time = _as_utc(now or datetime.now(timezone.utc))
    latest_reading: ReadingT | None = None
    latest_measured_at: datetime | None = None
    for reading in readings:
        if reading.quality == "invalid":
            continue
        measured_at = _as_utc(reading.measured_at)
        if max_age_seconds is not None:
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        if latest_measured_at is None or measured_at > latest_measured_at:
            latest_reading = reading
            latest_measured_at = measured_at
    return [latest_reading] if latest_reading is not None else []


def classify_latest_readings(
    readings_by_sensor: Mapping[str, Sequence[MeasuredReading]],
) -> tuple[list[str], list[str]]:
    """Return sensor names with invalid and suspect latest readings."""
    invalid_sensors = []
    suspect_sensors = []
    for sensor, readings in readings_by_sensor.items():
        if not readings:
            continue
        latest_reading = max(
            readings, key=lambda reading: _as_utc(reading.measured_at)
        )
        quality = latest_reading.quality
        if quality == "invalid":
            invalid_sensors.append(sensor)
        elif quality == "suspect":
            suspect_sensors.append(sensor)
    return invalid_sensors, suspect_sensors
