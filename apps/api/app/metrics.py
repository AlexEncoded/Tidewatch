from prometheus_client import Counter, Gauge


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

sensor_degraded = Gauge(
    "tidewatch_sensor_degraded",
    "Whether a sensor family is currently degraded (1) or healthy (0).",
    ["buoy_id", "sensor"],
)

buoy_last_seen_timestamp_seconds = Gauge(
    "tidewatch_buoy_last_seen_timestamp_seconds",
    "Unix timestamp of the most recent reading for each buoy.",
    ["buoy_id"],
)

reading_quality_total = Counter(
    "tidewatch_reading_quality_total",
    "Total sensor readings accepted by quality, family and channel.",
    ["buoy_id", "sensor_family", "sensor_channel", "quality"],
)
