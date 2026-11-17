from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Literal, Protocol, TypeVar, get_args

ReadingQuality = Literal["good", "suspect", "invalid"]
VALID_READING_QUALITIES = frozenset(get_args(ReadingQuality))


class MeasuredReading(Protocol):
    quality: ReadingQuality
    measured_at: datetime


ReadingT = TypeVar("ReadingT", bound=MeasuredReading)


def latest_usable_reading(
    readings: Sequence[ReadingT],
    max_age_seconds: float | None = None,
    now: datetime | None = None,
) -> list[ReadingT]:
    """Return the newest non-invalid reading within the optional age window."""
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    else:
        reference_time = reference_time.astimezone(timezone.utc)
    latest_reading: ReadingT | None = None
    latest_measured_at: datetime | None = None
    for reading in readings:
        if reading.quality == "invalid":
            continue
        measured_at = reading.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        else:
            measured_at = measured_at.astimezone(timezone.utc)
        if max_age_seconds is not None:
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        if latest_measured_at is None or measured_at > latest_measured_at:
            latest_reading = reading
            latest_measured_at = measured_at
    return [latest_reading] if latest_reading is not None else []


def classify_latest_readings(
    readings_by_sensor: Mapping[str, Sequence[object]],
) -> tuple[list[str], list[str]]:
    """Return sensor names with invalid and suspect latest readings."""
    invalid_sensors = []
    suspect_sensors = []
    for sensor, readings in readings_by_sensor.items():
        if not readings:
            continue
        quality = getattr(readings[0], "quality", None)
        if quality == "invalid":
            invalid_sensors.append(sensor)
        elif quality == "suspect":
            suspect_sensors.append(sensor)
    return invalid_sensors, suspect_sensors
