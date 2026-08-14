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


def run() -> None:
    with httpx.Client(timeout=10) as client:
        wait_for_api(client)
        buoy_id = find_or_create_buoy(client)
        current_temperature = BASE_TEMPERATURE
        current_pressure = BASE_PRESSURE
        current_salinity = BASE_SALINITY
        current_battery = BASE_BATTERY
        print(f"Simulating buoy {buoy_id} every {INTERVAL_SECONDS:g}s")

        while True:
            current_temperature = temperature_reading(current_temperature)
            current_pressure = pressure_reading(current_pressure)
            current_salinity = salinity_reading(current_salinity)
            current_battery = max(0, round(current_battery - random.uniform(0.01, 0.05), 2))
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
            for channel, values in readings.items():
                response = client.post(
                    f"{API_URL}/api/v1/buoys/{buoy_id}/temperatures",
                    json={
                        "temperature_celsius": values["temperature_celsius"],
                        "sensor_channel": channel,
                        "measured_at": measured_at,
                    },
                )
                response.raise_for_status()
                pressure_response = client.post(
                    f"{API_URL}/api/v1/buoys/{buoy_id}/pressures",
                    json={
                        "pressure_kpa": values["pressure_kpa"],
                        "sensor_channel": channel,
                        "measured_at": measured_at,
                    },
                )
                pressure_response.raise_for_status()
                salinity_response = client.post(
                    f"{API_URL}/api/v1/buoys/{buoy_id}/salinity",
                    json={
                        "salinity_psu": values["salinity_psu"],
                        "sensor_channel": channel,
                        "measured_at": measured_at,
                    },
                )
                salinity_response.raise_for_status()
            battery_response = client.post(
                f"{API_URL}/api/v1/buoys/{buoy_id}/battery",
                json={"battery_percent": current_battery, "measured_at": measured_at},
            )
            battery_response.raise_for_status()
            print(
                f"{buoy_id}: {current_temperature:.2f} °C | "
                f"{current_pressure:.3f} kPa | {current_salinity:.3f} PSU | "
                f"battery {current_battery:.1f}% | sensors A/B"
            )
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
