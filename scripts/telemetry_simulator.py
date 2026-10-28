"""Dependency-free simulator for a Tidewatch buoy with physical units A/B."""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url: str, method: str, payload: dict | None = None) -> dict | list:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def create_buoy(api_url: str, name: str) -> str:
    response = request_json(f"{api_url}/api/v1/buoys", "POST", {"name": name})
    assert isinstance(response, dict)
    return response["id"]


def ensure_simulator_devices(api_url: str, buoy_id: str) -> dict[str, dict]:
    """Ensure one registered physical unit exists for each redundant channel."""
    url = f"{api_url}/api/v1/buoys/{buoy_id}/devices"
    registered = request_json(url, "GET")
    if not isinstance(registered, list):
        raise ValueError("Device listing response must be a list")
    by_channel = {device["sensor_channel"]: device for device in registered}

    for channel in ("A", "B"):
        if channel in by_channel:
            continue
        try:
            created = request_json(
                url,
                "POST",
                {
                    "device_id": f"sim-{buoy_id}-{channel}",
                    "sensor_channel": channel,
                },
            )
            if not isinstance(created, dict):
                raise ValueError("Device registration response must be an object")
            by_channel[channel] = created
        except HTTPError as error:
            if error.code != 409:
                raise
            # Another simulator may have registered this channel concurrently.
            registered = request_json(url, "GET")
            if not isinstance(registered, list):
                raise ValueError("Device listing response must be a list") from None
            by_channel = {device["sensor_channel"]: device for device in registered}
            if channel not in by_channel:
                raise
    return {channel: by_channel[channel] for channel in ("A", "B")}


def build_payloads(devices: dict[str, dict]) -> dict[str, dict]:
    """Build synchronized redundant readings and per-device diagnostics."""
    now = datetime.now(timezone.utc)
    measured_at = now.isoformat()
    temperature = random.uniform(17.0, 24.0)
    pressure = random.uniform(100.8, 102.2)
    salinity = random.uniform(34.5, 38.0)
    wind_speed = random.uniform(0.0, 15.0)
    wind_direction = random.uniform(0.0, 360.0)
    current_speed = random.uniform(0.0, 3.0)
    current_direction = random.uniform(0.0, 360.0)
    turbidity = random.uniform(1.0, 400.0)
    dissolved_oxygen = random.uniform(6.0, 11.0)
    ph = random.uniform(7.8, 8.3)
    conductivity = random.uniform(48_000.0, 58_000.0)
    chlorophyll_a = random.uniform(0.5, 15.0)
    rainfall = 0.0 if random.random() < 0.75 else random.uniform(1.0, 25.0)
    humidity = random.uniform(60.0, 85.0)
    utc_hour = now.hour + now.minute / 60
    daylight = max(0.0, math.sin(math.pi * (utc_hour - 6) / 12))
    illuminance = 300 + 80_000 * daylight
    offsets = {"A": 0, "B": 1}
    payloads = {}
    for channel, device in devices.items():
        is_b = offsets[channel] == 1
        payloads[channel] = {
            "device_id": device["device_id"],
            "temperatures": [{
                "temperature_celsius": round(
                    temperature + (random.uniform(-0.15, 0.15) if is_b else 0), 2
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "pressures": [{
                "pressure_kpa": round(
                    pressure + (random.uniform(-0.08, 0.08) if is_b else 0), 3
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "salinity": [{
                "salinity_psu": round(
                    salinity + (random.uniform(-0.05, 0.05) if is_b else 0), 2
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "ambient_light": [{
                "illuminance_lux": round(
                    illuminance + (random.uniform(-150, 150) if is_b else 0), 1
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "wind": [{
                "wind_speed_mps": round(
                    wind_speed + (random.uniform(-0.1, 0.1) if is_b else 0), 2
                ),
                "wind_direction_degrees": round(
                    (wind_direction + (random.uniform(-3.0, 3.0) if is_b else 0))
                    % 360,
                    1,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "marine_current": [{
                "current_speed_mps": round(
                    current_speed + (random.uniform(-0.05, 0.05) if is_b else 0), 3
                ),
                "current_direction_degrees": round(
                    (current_direction + (random.uniform(-3.0, 3.0) if is_b else 0))
                    % 360,
                    1,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "turbidity": [{
                "turbidity_ntu": round(
                    turbidity + (random.uniform(-2.0, 2.0) if is_b else 0), 2
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "dissolved_oxygen": [{
                "dissolved_oxygen_mg_l": round(
                    dissolved_oxygen
                    + (random.uniform(-0.15, 0.15) if is_b else 0),
                    2,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "ph": [{
                "ph": round(ph + (random.uniform(-0.05, 0.05) if is_b else 0), 2),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "conductivity": [{
                "conductivity_us_cm": round(
                    conductivity + (random.uniform(-100.0, 100.0) if is_b else 0),
                    1,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "chlorophyll_a": [{
                "chlorophyll_a_ug_l": round(
                    chlorophyll_a + (random.uniform(-0.1, 0.1) if is_b else 0),
                    2,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "rainfall": [{
                "rainfall_mm_h": round(
                    rainfall + (random.uniform(-0.2, 0.2) if is_b and rainfall else 0),
                    2,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "humidity": [{
                "humidity_percent": round(
                    min(100.0, max(0.0, humidity + (random.uniform(-2.0, 2.0) if is_b else 0))),
                    1,
                ),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "imu": [{
                "acceleration_x_mps2": round(random.uniform(-0.3, 0.3), 3),
                "acceleration_y_mps2": round(random.uniform(-0.3, 0.3), 3),
                "acceleration_z_mps2": round(
                    9.81 + random.uniform(-0.05, 0.05), 3
                ),
                "angular_velocity_x_dps": round(random.uniform(-2.0, 2.0), 2),
                "angular_velocity_y_dps": round(random.uniform(-2.0, 2.0), 2),
                "angular_velocity_z_dps": round(random.uniform(-2.0, 2.0), 2),
                "sensor_channel": channel,
                "measured_at": measured_at,
            }],
            "battery": [{
                "battery_percent": round(random.uniform(70.0, 95.0), 1),
                "device_id": channel,
                "physical_device_id": device["device_id"],
                "measured_at": measured_at,
            }],
            "device_runtime": {
                "cpu_usage_percent": round(random.uniform(10.0, 75.0), 1),
                "memory_usage_percent": round(random.uniform(20.0, 85.0), 1),
                "measured_at": measured_at,
            },
            "device_communications": {
                "packet_loss_percent": round(random.uniform(0.0, 3.0), 2),
                "round_trip_latency_ms": round(random.uniform(40.0, 800.0), 1),
                "signal_strength_dbm": round(random.uniform(-100.0, -55.0), 1),
                "signal_to_noise_ratio_db": round(random.uniform(2.0, 30.0), 1),
                "measured_at": measured_at,
            },
        }
    return payloads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--buoy-id", help="Existing buoy ID; otherwise a buoy is created")
    parser.add_argument("--name", default="Local Test Buoy")
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--once", action="store_true", help="Send one batch and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than zero")

    buoy_id = args.buoy_id or create_buoy(args.api_url.rstrip("/"), args.name)
    api_url = args.api_url.rstrip("/")
    devices = ensure_simulator_devices(api_url, buoy_id)
    print(f"Simulating {buoy_id} against {api_url}")

    while True:
        payloads = build_payloads(devices)
        for channel, payload in payloads.items():
            try:
                result = request_json(
                    f"{api_url}/api/v1/buoys/{buoy_id}/telemetry",
                    "POST",
                    payload,
                )
                if not isinstance(result, dict):
                    raise ValueError("Telemetry response must be an object")
                if "accepted_readings" in result:
                    print(
                        f"Device {channel}: accepted {result['accepted_readings']} readings"
                    )
                else:
                    print(f"Device {channel}: queued job {result['job_id']}")
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
                print(f"Device {channel} telemetry send failed: {error}")

        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
