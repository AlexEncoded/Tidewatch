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
        current_battery_a = BASE_BATTERY
        current_battery_b = BASE_BATTERY
        current_latitude = BASE_LATITUDE
        current_longitude = BASE_LONGITUDE
        print(f"Simulating buoy {buoy_id} every {INTERVAL_SECONDS:g}s")

        while True:
            current_temperature = temperature_reading(current_temperature)
            current_pressure = pressure_reading(current_pressure)
            current_salinity = salinity_reading(current_salinity)
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
                f"battery A/B {current_battery_a:.1f}%/{current_battery_b:.1f}% | "
                f"position {current_latitude:.4f},{current_longitude:.4f} | sensors A/B"
            )
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
