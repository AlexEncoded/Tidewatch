"""Application services for maintenance issue classification."""

from collections.abc import Mapping, Sequence

from ..domain.reading_quality import classify_latest_readings
from ..models import MaintenanceIssue


def build_reading_quality_issues(
    buoy_id: str,
    buoy_name: str,
    latest_readings: Mapping[str, Sequence[object]],
) -> list[MaintenanceIssue]:
    """Build maintenance issues for invalid or suspect latest readings."""
    invalid_sensors, suspect_sensors = classify_latest_readings(latest_readings)
    issues: list[MaintenanceIssue] = []

    if invalid_sensors:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="invalid_reading",
                severity="warning",
                message=f"Invalid latest readings: {', '.join(invalid_sensors)}",
            )
        )

    if suspect_sensors:
        issues.append(
            MaintenanceIssue(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="suspect_reading",
                severity="warning",
                message=f"Suspect latest readings: {', '.join(suspect_sensors)}",
            )
        )

    return issues
