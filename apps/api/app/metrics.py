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

wind_readings_total = Counter(
    "tidewatch_wind_readings_total",
    "Total number of wind readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_wind_speed_mps = Gauge(
    "tidewatch_current_wind_speed_mps",
    "Most recent wind speed by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

current_wind_direction_degrees = Gauge(
    "tidewatch_current_wind_direction_degrees",
    "Most recent wind direction by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

marine_current_readings_total = Counter(
    "tidewatch_marine_current_readings_total",
    "Total number of marine current readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_marine_current_speed_mps = Gauge(
    "tidewatch_current_marine_current_speed_mps",
    "Most recent marine current speed by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

current_marine_current_direction_degrees = Gauge(
    "tidewatch_current_marine_current_direction_degrees",
    "Most recent marine current direction by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

turbidity_readings_total = Counter(
    "tidewatch_turbidity_readings_total",
    "Total number of turbidity readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_turbidity_ntu = Gauge(
    "tidewatch_current_turbidity_ntu",
    "Most recent turbidity in NTU by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

dissolved_oxygen_readings_total = Counter(
    "tidewatch_dissolved_oxygen_readings_total",
    "Total number of dissolved oxygen readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_dissolved_oxygen_mg_l = Gauge(
    "tidewatch_current_dissolved_oxygen_mg_l",
    "Most recent dissolved oxygen concentration in mg/L by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

ph_readings_total = Counter(
    "tidewatch_ph_readings_total",
    "Total number of pH readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_ph = Gauge(
    "tidewatch_current_ph",
    "Most recent pH value by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

conductivity_readings_total = Counter(
    "tidewatch_conductivity_readings_total",
    "Total number of conductivity readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_conductivity_us_cm = Gauge(
    "tidewatch_current_conductivity_us_cm",
    "Most recent conductivity in microsiemens per centimeter by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

chlorophyll_a_readings_total = Counter(
    "tidewatch_chlorophyll_a_readings_total",
    "Total number of chlorophyll-a readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_chlorophyll_a_ug_l = Gauge(
    "tidewatch_current_chlorophyll_a_ug_l",
    "Most recent chlorophyll-a concentration in micrograms per liter by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

rainfall_readings_total = Counter(
    "tidewatch_rainfall_readings_total",
    "Total number of rainfall readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_rainfall_mm_h = Gauge(
    "tidewatch_current_rainfall_mm_h",
    "Most recent rainfall intensity in mm/h by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

humidity_readings_total = Counter(
    "tidewatch_humidity_readings_total",
    "Total number of air humidity readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_humidity_percent = Gauge(
    "tidewatch_current_humidity_percent",
    "Most recent relative humidity by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

air_temperature_readings_total = Counter(
    "tidewatch_air_temperature_readings_total",
    "Total number of air temperature readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_air_temperature_celsius = Gauge(
    "tidewatch_current_air_temperature_celsius",
    "Most recent air temperature in Celsius by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

atmospheric_pressure_readings_total = Counter(
    "tidewatch_atmospheric_pressure_readings_total",
    "Total number of atmospheric pressure readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_atmospheric_pressure_kpa = Gauge(
    "tidewatch_current_atmospheric_pressure_kpa",
    "Most recent atmospheric pressure in kPa by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

acoustic_altimeter_readings_total = Counter(
    "tidewatch_acoustic_altimeter_readings_total",
    "Total number of acoustic altimeter readings accepted by the API.",
    ["buoy_id", "sensor_channel"],
)

current_acoustic_altimeter_depth_meters = Gauge(
    "tidewatch_current_acoustic_altimeter_depth_meters",
    "Most recent acoustic altimeter depth in meters by buoy and channel.",
    ["buoy_id", "sensor_channel"],
)

current_gnss_altitude_meters = Gauge(
    "tidewatch_current_gnss_altitude_meters",
    "Most recent GNSS altitude in meters by buoy.",
    ["buoy_id"],
)

current_gnss_speed_mps = Gauge(
    "tidewatch_current_gnss_speed_mps",
    "Most recent GNSS speed in meters per second by buoy.",
    ["buoy_id"],
)

current_gnss_hdop = Gauge(
    "tidewatch_current_gnss_hdop",
    "Most recent GNSS horizontal dilution of precision by buoy.",
    ["buoy_id"],
)

current_gnss_satellites = Gauge(
    "tidewatch_current_gnss_satellites",
    "Most recent GNSS satellite count by buoy.",
    ["buoy_id"],
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
