from datetime import datetime, timezone


def latest_usable_reading(
    readings: list,
    max_age_seconds: float | None = None,
    now: datetime | None = None,
) -> list:
    """Return the newest valid reading within the optional age window."""
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    for reading in readings:
        if reading.quality == "invalid":
            continue
        if max_age_seconds is not None:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=timezone.utc)
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        return [reading]
    return []
