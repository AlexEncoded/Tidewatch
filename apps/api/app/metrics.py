from prometheus_client import Counter, Gauge, Histogram


http_requests_total = Counter(
    "tidewatch_http_requests_total",
    "Total HTTP requests handled by method and response status.",
    ["method", "status_code"],
)

http_request_duration_seconds = Histogram(
    "tidewatch_http_request_duration_seconds",
    "HTTP request duration in seconds by method.",
    ["method"],
)

sensor_health_decision = Gauge(
    "tidewatch_sensor_health_decision",
    "Current sensor family decision: average, fallback_a, fallback_b or invalid.",
    ["buoy_id", "sensor", "decision"],
)


temperature_readings_total = Counter(
    "tidewatch_temperature_readings_total",
    "Total number of temperature readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_temperature_celsius = Gauge(
    "tidewatch_current_temperature_celsius",
    "Most recent temperature received for each buoy.",
    ["buoy_id", "sensor_channel"],
)

pressure_readings_total = Counter(
    "tidewatch_pressure_readings_total",
    "Total number of pressure readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_pressure_kpa = Gauge(
    "tidewatch_current_pressure_kpa",
    "Most recent pressure received for each buoy and sensor channel.",
    ["buoy_id", "sensor_channel"],
)

salinity_readings_total = Counter(
    "tidewatch_salinity_readings_total",
    "Total number of salinity readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_salinity_psu = Gauge(
    "tidewatch_current_salinity_psu",
    "Most recent salinity received for each buoy and sensor channel.",
    ["buoy_id", "sensor_channel"],
)

imu_readings_total = Counter(
    "tidewatch_imu_readings_total",
    "Total number of IMU readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_imu_acceleration_mps2 = Gauge(
    "tidewatch_current_imu_acceleration_mps2",
    "Most recent IMU acceleration vector component by buoy and channel.",
    ["buoy_id", "sensor_channel", "axis"],
)

current_imu_angular_velocity_dps = Gauge(
    "tidewatch_current_imu_angular_velocity_dps",
    "Most recent IMU angular velocity vector component by buoy and channel.",
    ["buoy_id", "sensor_channel", "axis"],
)

ambient_light_readings_total = Counter(
    "tidewatch_ambient_light_readings_total",
    "Total number of ambient light readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_ambient_light_lux = Gauge(
    "tidewatch_current_ambient_light_lux",
    "Most recent ambient light illuminance by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

sensor_degraded = Gauge(
    "tidewatch_sensor_degraded",
    "Whether a sensor family is currently degraded (1) or healthy (0).",
    ["buoy_id", "sensor"],
)

sensor_channel_missing = Gauge(
    "tidewatch_sensor_channel_missing",
    "Whether a redundant sensor channel is missing recent telemetry.",
    ["buoy_id", "sensor", "sensor_channel"],
)

buoy_last_seen_timestamp_seconds = Gauge(
    "tidewatch_buoy_last_seen_timestamp_seconds",
    "Unix timestamp of the most recent reading for each buoy.",
    ["buoy_id"],
)

battery_percent = Gauge(
    "tidewatch_battery_percent",
    "Most recent battery percentage for each buoy.",
    ["buoy_id"],
)

battery_device_percent = Gauge(
    "tidewatch_battery_device_percent",
    "Most recent battery percentage for each redundant buoy device.",
    ["buoy_id", "device_id"],
)

battery_delta_percent = Gauge(
    "tidewatch_battery_delta_percent",
    "Absolute battery percentage difference between redundant devices.",
    ["buoy_id"],
)

redundant_device_missing = Gauge(
    "tidewatch_redundant_device_missing",
    "Whether a redundant buoy device is missing battery telemetry.",
    ["buoy_id", "device_id"],
)

buoy_movement_speed_mps = Gauge(
    "tidewatch_buoy_movement_speed_mps",
    "Experimental average movement speed calculated from recent buoy positions.",
    ["buoy_id"],
)

reading_quality_total = Counter(
    "tidewatch_reading_quality_total",
    "Total sensor readings accepted by quality, family and channel.",
    ["buoy_id", "sensor_family", "sensor_channel", "quality"],
)
