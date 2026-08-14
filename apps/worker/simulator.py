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


def temperature_reading(previous: float) -> float:
    """Generate a small, realistic change from the previous reading."""
    drift = random.uniform(-0.25, 0.25)
    return round(max(-5, min(45, previous + drift)), 2)


def pressure_reading(previous: float) -> float:
    """Generate a realistic pressure change for the future wave model."""
    drift = random.uniform(-0.08, 0.08)
    return round(max(80, min(130, previous + drift)), 3)


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
        print(f"Simulating buoy {buoy_id} every {INTERVAL_SECONDS:g}s")

        while True:
            current_temperature = temperature_reading(current_temperature)
            current_pressure = pressure_reading(current_pressure)
            measured_at = datetime.now(timezone.utc).isoformat()
            payload = {
                "temperature_celsius": current_temperature,
                "measured_at": measured_at,
            }
            response = client.post(
                f"{API_URL}/api/v1/buoys/{buoy_id}/temperatures", json=payload
            )
            response.raise_for_status()
            pressure_response = client.post(
                f"{API_URL}/api/v1/buoys/{buoy_id}/pressures",
                json={"pressure_kpa": current_pressure, "measured_at": measured_at},
            )
            pressure_response.raise_for_status()
            print(f"{buoy_id}: {current_temperature:.2f} °C | {current_pressure:.3f} kPa")
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
