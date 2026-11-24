"""Public dependency provider facade for the HTTP application."""

from .operations import (
    get_quality_summary_reader,
    get_maintenance_reader,
    get_maintenance_metrics,
    get_maintenance_notification_job_store,
)
from ..adapters.http.system_dependencies import (
    get_database_health_reader,
    get_metrics_scraper,
    get_telemetry_queue_metrics_reader,
    get_telemetry_queue_metrics_publisher,
)
from .sensors import (
    get_sensor_health_reader,
    get_sensor_health_metrics,
    get_sensor_health_check_gateway,
    get_battery_telemetry_reader,
    get_battery_metrics,
    get_temperature_telemetry_gateway,
    get_pressure_telemetry_gateway,
    get_salinity_telemetry_gateway,
    get_imu_telemetry_gateway,
    get_ambient_light_telemetry_gateway,
    get_wind_telemetry_gateway,
    get_marine_current_telemetry_gateway,
    get_turbidity_telemetry_gateway,
    get_dissolved_oxygen_telemetry_gateway,
    get_ph_telemetry_gateway,
    get_conductivity_telemetry_gateway,
    get_chlorophyll_a_telemetry_gateway,
    get_rainfall_telemetry_gateway,
    get_humidity_telemetry_gateway,
    get_air_temperature_telemetry_gateway,
    get_atmospheric_pressure_telemetry_gateway,
    get_acoustic_altimeter_telemetry_gateway,
    get_underwater_acoustic_telemetry_gateway,
)
from .telemetry import (
    get_telemetry_ingestion_gateway,
    get_telemetry_batch_unit_of_work,
    get_telemetry_metrics,
    get_telemetry_ingestion_job_repository,
)
from .fleet import (
    get_buoy_summary_reader,
    get_fleet_location_reader,
    get_movement_analysis_reader,
    get_buoy_location_history_reader,
    get_stale_buoy_reader,
    get_buoy_status_registry,
    get_buoy_location_updater,
    get_buoy_registrar,
    get_fleet_metrics,
    get_device_registry,
    get_device_listing_reader,
    get_device_health_reader,
    get_device_status_registry,
)
from .analytics import (
    get_pressure_analysis_reader,
    get_wave_analysis_reader,
    get_wave_analysis_metrics,
    get_temperature_analysis_reader,
    get_temperature_alerts_reader,
    get_temperature_alert_store,
)
