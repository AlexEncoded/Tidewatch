"""Small persistence-adapter utilities shared across SQL repositories."""

from datetime import datetime, timezone


def is_newer_timestamp(candidate: datetime, previous: datetime | None) -> bool:
    """Compare timestamps consistently across PostgreSQL and SQLite."""
    if previous is None:
        return True
    candidate_utc = (
        candidate.astimezone(timezone.utc)
        if candidate.tzinfo
        else candidate.replace(tzinfo=timezone.utc)
    )
    previous_utc = (
        previous.astimezone(timezone.utc)
        if previous.tzinfo
        else previous.replace(tzinfo=timezone.utc)
    )
    return candidate_utc > previous_utc
