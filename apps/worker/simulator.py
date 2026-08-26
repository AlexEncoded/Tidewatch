import os
import random
import time
from datetime import datetime, timezone

import httpx


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
BUOY_NAME = os.getenv("BUOY_NAME", "Mediterranean Sentinel")
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "10"))
BASE_TEMPERATURE = float(os.getenv("BASE_TEMPERATURE_CELSIUS", "19.5"))
BASE_PRESSURE = float(os.getenv("BASE_PRESSURE_KPA", "101.3"))
BASE_SALINITY = float(os.getenv("BASE_SALINITY_PSU", "35.2"))
BASE_AMBIENT_LIGHT = float(os.getenv("BASE_AMBIENT_LIGHT_LUX", "1200"))
BASE_WIND_SPEED = float(os.getenv("BASE_WIND_SPEED_MPS", "4"))
BASE_WIND_DIRECTION = float(os.getenv("BASE_WIND_DIRECTION_DEGREES", "180"))
BASE_CURRENT_SPEED = float(os.getenv("BASE_CURRENT_SPEED_MPS", "0.8"))
BASE_CURRENT_DIRECTION = float(os.getenv("BASE_CURRENT_DIRECTION_DEGREES", "90"))
BASE_TURBIDITY = float(os.getenv("BASE_TURBIDITY_NTU", "3"))
BASE_DISSOLVED_OXYGEN = float(os.getenv("BASE_DISSOLVED_OXYGEN_MG_L", "7.5"))
BASE_PH = float(os.getenv("BASE_PH", "8.1"))
BASE_CONDUCTIVITY = float(os.getenv("BASE_CONDUCTIVITY_US_CM", "51000"))
BASE_CHLOROPHYLL_A = float(os.getenv("BASE_CHLOROPHYLL_A_UG_L", "4.2"))
BASE_RAINFALL = float(os.getenv("BASE_RAINFALL_MM_H", "0"))
BASE_HUMIDITY = float(os.getenv("BASE_HUMIDITY_PERCENT", "75"))
BASE_AIR_TEMPERATURE = float(os.getenv("BASE_AIR_TEMPERATURE_CELSIUS", "24"))
BASE_ATMOSPHERIC_PRESSURE = float(os.getenv("BASE_ATMOSPHERIC_PRESSURE_KPA", "101.3"))
BASE_ACOUSTIC_ALTIMETER_DEPTH = float(os.getenv("BASE_ACOUSTIC_ALTIMETER_DEPTH_METERS", "12"))
BASE_BATTERY = float(os.getenv("BASE_BATTERY_PERCENT", "100"))
BASE_LATITUDE = float(os.getenv("BASE_LATITUDE", "36.7"))
BASE_LONGITUDE = float(os.getenv("BASE_LONGITUDE", "3.1"))
TELEMETRY_RETRIES = max(0, int(os.getenv("TELEMETRY_RETRIES", "3")))
RETRY_BACKOFF_SECONDS = max(0, float(os.getenv("RETRY_BACKOFF_SECONDS", "1")))
SENSOR_FIRMWARE_VERSION = os.getenv("SENSOR_FIRMWARE_VERSION", "2.4.1")


def temperature_reading(previous: float) -> float:
    """Generate a small, realistic change from the previous reading."""
    drift = random.uniform(-0.25, 0.25)
    return round(max(-5, min(45, previous + drift)), 2)


def pressure_reading(previous: float) -> float:
    """Generate a realistic pressure change for the future wave model."""
    drift = random.uniform(-0.08, 0.08)
    return round(max(80, min(130, previous + drift)), 3)


def salinity_reading(previous: float) -> float:
    """Generate a small salinity change in practical salinity units."""
    drift = random.uniform(-0.03, 0.03)
    return round(max(0, min(45, previous + drift)), 3)


def imu_reading() -> dict[str, float]:
    """Generate a calm buoy IMU vector with gravity on the vertical axis."""
    return {
        "acceleration_x_mps2": round(random.uniform(-0.35, 0.35), 3),
        "acceleration_y_mps2": round(random.uniform(-0.35, 0.35), 3),
        "acceleration_z_mps2": round(random.uniform(9.65, 9.95), 3),
        "angular_velocity_x_dps": round(random.uniform(-2.0, 2.0), 3),
        "angular_velocity_y_dps": round(random.uniform(-2.0, 2.0), 3),
        "angular_velocity_z_dps": round(random.uniform(-2.0, 2.0), 3),
    }


def ambient_light_reading(previous: float) -> float:
    """Simulate gradual daylight changes in lux."""
    return round(max(0, min(150000, previous + random.uniform(-180, 180))), 2)


def wind_reading(previous_speed: float, previous_direction: float) -> dict[str, float]:
    """Simulate wind with a bounded speed and circular direction."""
    return {
        "wind_speed_mps": round(max(0, min(100, previous_speed + random.uniform(-0.5, 0.5))), 2),
        "wind_direction_degrees": round(
            (previous_direction + random.uniform(-8, 8)) % 360, 2
        ),
    }


def marine_current_reading(
    previous_speed: float, previous_direction: float
) -> dict[str, float]:
    """Simulate a bounded marine current with circular direction."""
    return {
        "current_speed_mps": round(
            max(0, min(20, previous_speed + random.uniform(-0.08, 0.08))), 3
        ),
        "current_direction_degrees": round(
            (previous_direction + random.uniform(-4, 4)) % 360, 2
        ),
    }


def turbidity_reading(previous: float) -> float:
    """Simulate gradual suspended-particle changes in NTU."""
    return round(max(0, min(5000, previous + random.uniform(-0.4, 0.4))), 3)


def dissolved_oxygen_reading(previous: float) -> float:
    """Simulate gradual dissolved oxygen changes in mg/L."""
    return round(max(0, min(20, previous + random.uniform(-0.08, 0.08))), 3)


def ph_reading(previous: float) -> float:
    """Simulate gradual seawater pH changes within the sensor range."""
    return round(max(0, min(14, previous + random.uniform(-0.02, 0.02))), 3)


def conductivity_reading(previous: float) -> float:
    """Simulate gradual conductivity changes in microsiemens per centimeter."""
    return round(max(0, min(200000, previous + random.uniform(-250, 250))), 2)


def chlorophyll_a_reading(previous: float) -> float:
    """Simulate gradual chlorophyll-a changes in micrograms per liter."""
    return round(max(0, min(1000, previous + random.uniform(-0.2, 0.2))), 3)


def rainfall_reading(previous: float) -> float:
    """Simulate bounded rainfall intensity in millimeters per hour."""
    return round(max(0, min(500, previous + random.uniform(-2, 2))), 2)


def humidity_reading(previous: float) -> float:
    """Simulate gradual relative humidity changes."""
    return round(max(0, min(100, previous + random.uniform(-1, 1))), 2)


def air_temperature_reading(previous: float) -> float:
    """Simulate gradual air temperature changes."""
    return round(max(-60, min(60, previous + random.uniform(-0.3, 0.3))), 2)


def atmospheric_pressure_reading(previous: float) -> float:
    """Simulate gradual atmospheric pressure changes."""
    return round(max(80, min(120, previous + random.uniform(-0.08, 0.08))), 3)


def acoustic_altimeter_reading(previous: float) -> float:
    """Simulate a bounded acoustic depth measurement in meters."""
    return round(max(0, min(20000, previous + random.uniform(-0.2, 0.2))), 3)


def battery_reading(previous: float) -> float:
    """Simulate gradual battery discharge for one physical buoy device."""
    return max(0, round(previous - random.uniform(0.01, 0.05), 2))


def wait_for_api(client: httpx.Client) -> None:
    while True:
        try:
            response = client.get(f"{API_URL}/health")
            response.raise_for_status()
            return
        except httpx.HTTPError:
            print("Waiting for Tidewatch API...")
            time.sleep(2)


def find_or_create_buoy(client: httpx.Client) -> str:
    response = client.get(f"{API_URL}/api/v1/buoys")
    response.raise_for_status()
    buoys = response.json()

    for item in buoys:
        if item["buoy"]["name"] == BUOY_NAME:
            return item["buoy"]["id"]

    response = client.post(f"{API_URL}/api/v1/buoys", json={"name": BUOY_NAME})
    response.raise_for_status()
    return response.json()["id"]


def send_telemetry(client: httpx.Client, buoy_id: str, payload: dict) -> None:
    for attempt in range(TELEMETRY_RETRIES + 1):
        try:
            response = client.post(
                f"{API_URL}/api/v1/buoys/{buoy_id}/telemetry",
                json=payload,
            )
            if response.status_code < 500:
                response.raise_for_status()
                return
            error = httpx.HTTPStatusError(
                f"Server returned {response.status_code}",
                request=response.request,
                response=response,
            )
        except httpx.RequestError as error:
            if attempt >= TELEMETRY_RETRIES:
                raise

        delay = RETRY_BACKOFF_SECONDS * (2**attempt)
        print(f"Telemetry send failed ({error}); retrying in {delay:g}s")
        time.sleep(delay)

    raise error


def run() -> None:
    with httpx.Client(timeout=10) as client:
        wait_for_api(client)
        buoy_id = find_or_create_buoy(client)
        current_temperature = BASE_TEMPERATURE
        current_pressure = BASE_PRESSURE
        current_salinity = BASE_SALINITY
        current_ambient_light = BASE_AMBIENT_LIGHT
        current_wind_speed = BASE_WIND_SPEED
        current_wind_direction = BASE_WIND_DIRECTION
        current_current_speed = BASE_CURRENT_SPEED
        current_current_direction = BASE_CURRENT_DIRECTION
        current_turbidity = BASE_TURBIDITY
        current_dissolved_oxygen = BASE_DISSOLVED_OXYGEN
        current_ph = BASE_PH
        current_conductivity = BASE_CONDUCTIVITY
        current_chlorophyll_a = BASE_CHLOROPHYLL_A
        current_rainfall = BASE_RAINFALL
        current_humidity = BASE_HUMIDITY
        current_air_temperature = BASE_AIR_TEMPERATURE
        current_atmospheric_pressure = BASE_ATMOSPHERIC_PRESSURE
        current_acoustic_altimeter_depth = BASE_ACOUSTIC_ALTIMETER_DEPTH
        current_battery_a = BASE_BATTERY
        current_battery_b = BASE_BATTERY
        current_latitude = BASE_LATITUDE
        current_longitude = BASE_LONGITUDE
        print(f"Simulating buoy {buoy_id} every {INTERVAL_SECONDS:g}s")

        while True:
            current_temperature = temperature_reading(current_temperature)
            current_pressure = pressure_reading(current_pressure)
            current_salinity = salinity_reading(current_salinity)
            current_ambient_light = ambient_light_reading(current_ambient_light)
            wind_a = wind_reading(current_wind_speed, current_wind_direction)
            current_wind_speed = wind_a["wind_speed_mps"]
            current_wind_direction = wind_a["wind_direction_degrees"]
            wind_b = {
                "wind_speed_mps": round(max(0, wind_a["wind_speed_mps"] + random.uniform(-0.1, 0.1)), 2),
                "wind_direction_degrees": round(
                    (wind_a["wind_direction_degrees"] + random.uniform(-2, 2)) % 360,
                    2,
                ),
            }
            current_a = marine_current_reading(
                current_current_speed, current_current_direction
            )
            current_current_speed = current_a["current_speed_mps"]
            current_current_direction = current_a["current_direction_degrees"]
            current_b = {
                "current_speed_mps": round(
                    max(0, current_a["current_speed_mps"] + random.uniform(-0.03, 0.03)),
                    3,
                ),
                "current_direction_degrees": round(
                    (current_a["current_direction_degrees"] + random.uniform(-1, 1)) % 360,
                    2,
                ),
            }
            current_turbidity = turbidity_reading(current_turbidity)
            current_dissolved_oxygen = dissolved_oxygen_reading(current_dissolved_oxygen)
            current_ph = ph_reading(current_ph)
            current_conductivity = conductivity_reading(current_conductivity)
            current_chlorophyll_a = chlorophyll_a_reading(current_chlorophyll_a)
            current_rainfall = rainfall_reading(current_rainfall)
            current_humidity = humidity_reading(current_humidity)
            current_air_temperature = air_temperature_reading(current_air_temperature)
            current_atmospheric_pressure = atmospheric_pressure_reading(current_atmospheric_pressure)
            current_acoustic_altimeter_depth = acoustic_altimeter_reading(current_acoustic_altimeter_depth)
            imu_a = imu_reading()
            imu_b = {
                key: round(value + random.uniform(-0.04, 0.04), 3)
                for key, value in imu_a.items()
            }
            current_battery_a = battery_reading(current_battery_a)
            current_battery_b = battery_reading(current_battery_b)
            current_latitude = max(-90, min(90, current_latitude + random.uniform(-0.001, 0.001)))
            current_longitude = max(-180, min(180, current_longitude + random.uniform(-0.001, 0.001)))
            measured_at = datetime.now(timezone.utc).isoformat()
            readings = {
                "A": {
                    "temperature_celsius": current_temperature,
                    "pressure_kpa": current_pressure,
                    "salinity_psu": current_salinity,
                },
                "B": {
                    "temperature_celsius": round(current_temperature + random.uniform(-0.04, 0.04), 2),
                    "pressure_kpa": round(current_pressure + random.uniform(-0.12, 0.12), 3),
                    "salinity_psu": round(current_salinity + random.uniform(-0.04, 0.04), 3),
                },
            }
            payload = {
                "temperatures": [
                    {
                        "temperature_celsius": values["temperature_celsius"],
                        "sensor_channel": channel,
                        "sensor_id": f"temperature-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel, values in readings.items()
                ],
                "pressures": [
                    {
                        "pressure_kpa": values["pressure_kpa"],
                        "sensor_channel": channel,
                        "sensor_id": f"pressure-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel, values in readings.items()
                ],
                "salinity": [
                    {
                        "salinity_psu": values["salinity_psu"],
                        "sensor_channel": channel,
                        "sensor_id": f"salinity-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel, values in readings.items()
                ],
                "imu": [
                    {
                        **values,
                        "sensor_channel": channel,
                        "sensor_id": f"imu-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel, values in {"A": imu_a, "B": imu_b}.items()
                ],
                "ambient_light": [
                    {
                        "illuminance_lux": round(
                            current_ambient_light
                            + (0 if channel == "A" else random.uniform(-25, 25)),
                            2,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"ambient-light-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "wind": [
                    {
                        **values,
                        "sensor_channel": channel,
                        "sensor_id": f"wind-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel, values in {"A": wind_a, "B": wind_b}.items()
                ],
                "marine_current": [
                    {
                        **values,
                        "sensor_channel": channel,
                        "sensor_id": f"marine-current-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel, values in {"A": current_a, "B": current_b}.items()
                ],
                "turbidity": [
                    {
                        "turbidity_ntu": round(
                            max(
                                0,
                                current_turbidity
                                + (0 if channel == "A" else random.uniform(-0.15, 0.15)),
                            ),
                            3,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"turbidity-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "dissolved_oxygen": [
                    {
                        "dissolved_oxygen_mg_l": round(
                            max(
                                0,
                                min(
                                    20,
                                    current_dissolved_oxygen
                                    + (0 if channel == "A" else random.uniform(-0.03, 0.03)),
                                ),
                            ),
                            3,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"dissolved-oxygen-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "ph": [
                    {
                        "ph": round(
                            max(
                                0,
                                min(
                                    14,
                                    current_ph
                                    + (0 if channel == "A" else random.uniform(-0.01, 0.01)),
                                ),
                            ),
                            3,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"ph-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "conductivity": [
                    {
                        "conductivity_us_cm": round(
                            max(
                                0,
                                min(
                                    200000,
                                    current_conductivity
                                    + (0 if channel == "A" else random.uniform(-80, 80)),
                                ),
                            ),
                            2,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"conductivity-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "chlorophyll_a": [
                    {
                        "chlorophyll_a_ug_l": round(
                            max(
                                0,
                                min(
                                    1000,
                                    current_chlorophyll_a
                                    + (0 if channel == "A" else random.uniform(-0.05, 0.05)),
                                ),
                            ),
                            3,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"chlorophyll-a-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "rainfall": [
                    {
                        "rainfall_mm_h": round(
                            max(
                                0,
                                min(
                                    500,
                                    current_rainfall
                                    + (0 if channel == "A" else random.uniform(-0.5, 0.5)),
                                ),
                            ),
                            2,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"rain-gauge-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "humidity": [
                    {
                        "humidity_percent": round(
                            max(
                                0,
                                min(
                                    100,
                                    current_humidity
                                    + (0 if channel == "A" else random.uniform(-0.8, 0.8)),
                                ),
                            ),
                            2,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"humidity-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "air_temperature": [
                    {
                        "air_temperature_celsius": round(
                            current_air_temperature
                            + (0 if channel == "A" else random.uniform(-0.15, 0.15)),
                            2,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"air-temperature-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "atmospheric_pressure": [
                    {
                        "atmospheric_pressure_kpa": round(
                            current_atmospheric_pressure
                            + (0 if channel == "A" else random.uniform(-0.04, 0.04)),
                            3,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"barometer-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "acoustic_altimeter": [
                    {
                        "depth_meters": round(
                            current_acoustic_altimeter_depth
                            + (0 if channel == "A" else random.uniform(-0.05, 0.05)),
                            3,
                        ),
                        "sensor_channel": channel,
                        "sensor_id": f"acoustic-altimeter-{channel.lower()}-01",
                        "firmware_version": SENSOR_FIRMWARE_VERSION,
                        "measured_at": measured_at,
                    }
                    for channel in ("A", "B")
                ],
                "battery": [
                    {
                        "battery_percent": current_battery_a,
                        "device_id": "A",
                        "measured_at": measured_at,
                    },
                    {
                        "battery_percent": current_battery_b,
                        "device_id": "B",
                        "measured_at": measured_at,
                    },
                ],
                "location": {
                    "latitude": round(current_latitude, 6),
                    "longitude": round(current_longitude, 6),
                },
            }
            send_telemetry(client, buoy_id, payload)
            print(
                f"{buoy_id}: {current_temperature:.2f} °C | "
                f"{current_pressure:.3f} kPa | {current_salinity:.3f} PSU | "
                f"light {current_ambient_light:.1f} lux | "
                f"wind {current_wind_speed:.2f} m/s {current_wind_direction:.1f}° | "
                f"current {current_current_speed:.3f} m/s {current_current_direction:.1f}° | "
                f"turbidity {current_turbidity:.3f} NTU | "
                f"dissolved oxygen {current_dissolved_oxygen:.3f} mg/L | "
                f"pH {current_ph:.3f} | "
                f"conductivity {current_conductivity:.2f} uS/cm | "
                f"chlorophyll-a {current_chlorophyll_a:.3f} ug/L | "
                f"rainfall {current_rainfall:.2f} mm/h | "
                f"humidity {current_humidity:.2f}% | "
                f"air temperature {current_air_temperature:.2f} C | "
                f"atmospheric pressure {current_atmospheric_pressure:.3f} kPa | "
                f"acoustic depth {current_acoustic_altimeter_depth:.3f} m | "
                f"battery A/B {current_battery_a:.1f}%/{current_battery_b:.1f}% | "
                f"position {current_latitude:.4f},{current_longitude:.4f} | sensors A/B"
            )
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
