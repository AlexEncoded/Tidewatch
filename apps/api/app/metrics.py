from prometheus_client import Counter, Gauge


temperature_readings_total = Counter(
    "tidewatch_temperature_readings_total",
    "Total number of temperature readings accepted by the API.",
    ["buoy_id"],
)

current_temperature_celsius = Gauge(
    "tidewatch_current_temperature_celsius",
    "Most recent temperature received for each buoy.",
    ["buoy_id"],
)

buoy_last_seen_timestamp_seconds = Gauge(
    "tidewatch_buoy_last_seen_timestamp_seconds",
    "Unix timestamp of the most recent reading for each buoy.",
    ["buoy_id"],
)
