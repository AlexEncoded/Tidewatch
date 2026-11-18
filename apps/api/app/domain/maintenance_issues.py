"""Application services for maintenance issue classification."""

from collections.abc import Mapping, Sequence
from datetime import datetime

from ..domain.battery_health import BatteryHealthSnapshot
from ..domain.buoy import BuoyOperationalStatus
from ..domain.sensor_health import SensorHealthSnapshot
from ..domain.maintenance import is_buoy_drifting, is_buoy_silent
from ..domain.device_health import DeviceHealthSnapshot
from ..domain.reading_quality import MeasuredReading, classify_latest_readings
from ..domain.sensor_health import SensorHealthSnapshot
from ..domain.maintenance import (
    MaintenanceIssueSnapshot,
    low_battery_severity,
    missing_redundant_battery_device,
)

_SENSOR_DELTA_DETAILS = {
    "temperature": ("temperature_delta_celsius", "°C", "temperature"),
    "pressure": ("pressure_delta_kpa", "kPa", "pressure"),
    "salinity": ("salinity_delta_psu", "PSU", "salinity"),
    "imu": ("imu_acceleration_delta_mps2", "m/s²", "imu"),
    "ambient_light": ("ambient_light_delta_lux", "lux", "ambient_light"),
    "wind_speed": ("wind_speed_delta_mps", "m/s", "wind"),
    "wind_direction": ("wind_direction_delta_degrees", "°", "wind"),
    "marine_current_speed": (
        "marine_current_speed_delta_mps",
        "m/s",
        "marine_current",
    ),
    "marine_current_direction": (
        "marine_current_direction_delta_degrees",
        "°",
        "marine_current",
    ),
    "turbidity": ("turbidity_delta_ntu", "NTU", "turbidity"),
    "dissolved_oxygen": (
        "dissolved_oxygen_delta_mg_l",
        "mg/L",
        "dissolved_oxygen",
    ),
    "ph": ("ph_delta", "pH", "ph"),
    "conductivity": ("conductivity_delta_us_cm", "µS/cm", "conductivity"),
    "chlorophyll_a": ("chlorophyll_a_delta_ug_l", "µg/L", "chlorophyll_a"),
    "rainfall": ("rainfall_delta_mm_h", "mm/h", "rainfall"),
    "humidity": ("humidity_delta_percent", "percentage points", "humidity"),
    "air_temperature": (
        "air_temperature_delta_celsius",
        "°C",
        "air_temperature",
    ),
    "atmospheric_pressure": (
        "atmospheric_pressure_delta_kpa",
        "kPa",
        "atmospheric_pressure",
    ),
    "acoustic_altimeter": (
        "acoustic_altimeter_delta_meters",
        "m",
        "acoustic_altimeter",
    ),
    "underwater_acoustic": (
        "underwater_acoustic_delta_db",
        "dB",
        "underwater_acoustic",
    ),
}


def _describe_degraded_sensors(health: SensorHealthSnapshot) -> str:
    degraded = health.degraded_sensors or []
    descriptions = []
    for sensor in degraded:
        details = _SENSOR_DELTA_DETAILS.get(sensor)
        if details is None:
            if sensor == "wind" and any(
                name in degraded for name in ("wind_speed", "wind_direction")
            ):
                continue
            if sensor == "marine_current" and any(
                name in degraded
                for name in ("marine_current_speed", "marine_current_direction")
            ):
                continue
            descriptions.append(sensor)
            continue

        attribute, unit, family = details
        delta = getattr(health, attribute)
        decision = (health.decisions or {}).get(family)
        description = sensor
        if delta is not None:
            description += f" (A/B delta {delta:g} {unit}"
            if decision == "fallback_a":
                description += "; selected A)"
            elif decision == "fallback_b":
                description += "; selected B)"
            elif decision == "invalid":
                description += "; no channel selected)"
            else:
                description += ")"
        descriptions.append(description)
    return ", ".join(descriptions)


def build_reading_quality_issues(
    buoy_id: str,
    buoy_name: str,
    latest_readings: Mapping[str, Sequence[MeasuredReading]],
) -> list[MaintenanceIssueSnapshot]:
    """Build maintenance issues for invalid or suspect latest readings."""
    invalid_sensors, suspect_sensors = classify_latest_readings(latest_readings)
    issues: list[MaintenanceIssueSnapshot] = []

    if invalid_sensors:
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="invalid_reading",
                severity="warning",
                message=f"Invalid latest readings: {', '.join(invalid_sensors)}",
            )
        )

    if suspect_sensors:
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="suspect_reading",
                severity="warning",
                message=f"Suspect latest readings: {', '.join(suspect_sensors)}",
            )
        )

    return issues


def build_battery_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    latest_batteries: Mapping[str, object | None],
    health: BatteryHealthSnapshot,
) -> list[MaintenanceIssueSnapshot]:
    """Build maintenance issues from redundant battery readings and health."""
    issues: list[MaintenanceIssueSnapshot] = []
    for device_id in ("A", "B"):
        battery = latest_batteries.get(device_id)
        battery_percent = getattr(battery, "battery_percent", None)
        severity = (
            low_battery_severity(battery_percent)
            if battery_percent is not None
            else None
        )
        if severity is not None:
            issues.append(
                MaintenanceIssueSnapshot(
                    buoy_id=buoy_id,
                    buoy_name=buoy_name,
                    issue_type="low_battery",
                    severity=severity,
                    message=(
                        f"Battery level for device {device_id} is "
                        f"{battery_percent:.1f}%"
                    ),
                )
            )

    missing_device = missing_redundant_battery_device(
        health.device_a_percent, health.device_b_percent
    )
    if missing_device is not None:
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="missing_redundant_device",
                severity="warning",
                message=(
                    f"No battery telemetry received from redundant device {missing_device}"
                ),
            )
        )

    if health.status == "degraded":
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="degraded_battery",
                severity="warning",
                message=(
                    f"Battery units diverge by {health.delta_percent:.1f}% "
                    f"(unit {', '.join(health.degraded_devices)} suspected)"
                ),
            )
        )

    return issues


def build_operational_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    status: BuoyOperationalStatus,
    last_seen_at: datetime | None,
    now: datetime,
    max_age_minutes: float,
    average_speed_mps: float | None,
    drift_speed_mps: float,
) -> list[MaintenanceIssueSnapshot]:
    """Build maintenance issues for silence and unexpected buoy movement."""
    issues: list[MaintenanceIssueSnapshot] = []
    if is_buoy_silent(status, last_seen_at, now, max_age_minutes * 60):
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="silent_buoy",
                severity="warning",
                message=(
                    f"No telemetry received for more than {max_age_minutes:g} minutes"
                ),
            )
        )

    if is_buoy_drifting(average_speed_mps, drift_speed_mps):
        issues.append(
                MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="drift_detected",
                severity="warning",
                message=(
                    f"Average movement speed is {average_speed_mps:.3f} m/s, "
                    f"above the configured limit of {drift_speed_mps:g} m/s"
                ),
            )
        )

    return issues


def build_sensor_health_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    health: SensorHealthSnapshot,
) -> list[MaintenanceIssueSnapshot]:
    """Build maintenance issues for degraded or missing sensor channels."""
    if health.status != "degraded":
        return []

    issues: list[MaintenanceIssueSnapshot] = []
    if health.degraded_sensors:
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="degraded_sensor",
                severity="warning",
                message=f"Degraded sensors: {_describe_degraded_sensors(health)}",
            )
        )
    if health.missing_sensors:
        issues.append(
            MaintenanceIssueSnapshot(
                buoy_id=buoy_id,
                buoy_name=buoy_name,
                issue_type="missing_sensor_channel",
                severity="warning",
                message=(
                    "No recent telemetry received from sensor channels: "
                    f"{', '.join(health.missing_sensors)}"
                ),
            )
        )
    return issues


def build_device_maintenance_issues(
    buoy_id: str,
    buoy_name: str,
    devices: Sequence[DeviceHealthSnapshot],
) -> list[MaintenanceIssueSnapshot]:
    """Build maintenance issues for physical devices without a heartbeat."""
    return [
        MaintenanceIssueSnapshot(
            buoy_id=buoy_id,
            buoy_name=buoy_name,
            issue_type="stale_device",
            severity="warning",
            message=(
                f"Physical device {device.device_id} "
                f"(channel {device.sensor_channel}) has no recent heartbeat"
            ),
        )
        for device in devices
        if device.is_stale
    ]


def build_maintenance_issues_for_buoy(
    buoy_id: str,
    buoy_name: str,
    status: BuoyOperationalStatus,
    last_seen_at: datetime | None,
    now: datetime,
    max_age_minutes: float,
    drift_speed_mps: float,
    sensor_health: SensorHealthSnapshot,
    latest_readings: Mapping[str, Sequence[MeasuredReading]],
    latest_batteries: Mapping[str, object | None],
    battery_health: BatteryHealthSnapshot,
    average_speed_mps: float | None,
    device_health: Sequence[DeviceHealthSnapshot] = (),
) -> list[MaintenanceIssueSnapshot]:
    """Compose all maintenance issue types for one buoy snapshot."""
    issues = build_sensor_health_maintenance_issues(
        buoy_id, buoy_name, sensor_health
    )
    issues.extend(build_device_maintenance_issues(buoy_id, buoy_name, device_health))
    issues.extend(build_reading_quality_issues(buoy_id, buoy_name, latest_readings))
    issues.extend(
        build_battery_maintenance_issues(
            buoy_id, buoy_name, latest_batteries, battery_health
        )
    )
    issues.extend(
        build_operational_maintenance_issues(
            buoy_id,
            buoy_name,
            status,
            last_seen_at,
            now,
            max_age_minutes,
            average_speed_mps,
            drift_speed_mps,
        )
    )
    return issues
