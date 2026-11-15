"""Shared validation for location-history query windows."""

from datetime import datetime


class InvalidLocationTimeRange(ValueError):
    """The start of a location-history range is later than its end."""


def validate_location_time_range(
    since: datetime | None, until: datetime | None
) -> None:
    """Reject location-history windows whose start follows their end."""
    if since is not None and until is not None and since > until:
        raise InvalidLocationTimeRange(
            "since must be earlier than or equal to until"
        )
