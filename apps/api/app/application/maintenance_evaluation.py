"""Application service for evaluating maintenance state per buoy."""

from dataclasses import dataclass
from datetime import datetime

from .battery_health import analyze_battery_health_for_buoy
from .device_health import summarize_device_health_for_buoy
from .maintenance_issues import build_maintenance_issues_for_buoy
from .movement_analysis import analyze_movement_for_buoy
from .ports import MaintenanceReader
from .sensor_health import evaluate_sensor_health_snapshot
from ..models import BatteryHealth, MaintenanceIssue


@dataclass(frozen=True)
class MaintenanceBuoyEvaluation:
    """Maintenance result plus values needed by the metrics adapter."""

    issues: list[MaintenanceIssue]
    battery_health: BatteryHealth
    average_speed_mps: float | None


def evaluate_maintenance_fleet(
    reader: MaintenanceReader,
    now: datetime,
    max_age_minutes: float,
    drift_speed_mps: float,
) -> list[tuple[object, MaintenanceBuoyEvaluation]]:
    """Evaluate every buoy through the maintenance input port."""
    return [
        (
            buoy,
            evaluate_maintenance_buoy(
                reader, buoy, now, max_age_minutes, drift_speed_mps
            ),
        )
        for buoy in reader.list_buoys()
    ]


def evaluate_maintenance_buoy(
    reader: MaintenanceReader,
    buoy: object,
    now: datetime,
    max_age_minutes: float,
    drift_speed_mps: float,
) -> MaintenanceBuoyEvaluation:
    """Evaluate all maintenance rules for one buoy through application ports."""
    buoy_id = buoy.id
    sensor_health = evaluate_sensor_health_snapshot(
        reader, buoy_id, max_age_minutes * 60, now
    ).health
    latest_readings = {
        "temperature": reader.list_temperatures(buoy_id, 1),
        "pressure": reader.list_pressures(buoy_id, 1),
        "salinity": reader.list_salinity(buoy_id, 1),
    }
    battery_health = analyze_battery_health_for_buoy(reader, buoy_id, 10)
    latest_batteries = {
        device_id: reader.latest_battery(buoy_id, device_id)
        for device_id in ("A", "B")
    }
    movement = analyze_movement_for_buoy(reader, buoy_id, 50)
    device_health = summarize_device_health_for_buoy(
        reader, buoy_id, now, max_age_minutes * 60
    )
    issues = build_maintenance_issues_for_buoy(
        buoy_id,
        buoy.name,
        buoy.status,
        buoy.last_seen_at,
        now,
        max_age_minutes,
        drift_speed_mps,
        sensor_health,
        latest_readings,
        latest_batteries,
        battery_health,
        movement.average_speed_mps,
        device_health,
    )
    return MaintenanceBuoyEvaluation(
        issues=issues,
        battery_health=battery_health,
        average_speed_mps=movement.average_speed_mps,
    )
