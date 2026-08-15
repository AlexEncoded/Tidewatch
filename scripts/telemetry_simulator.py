"""Small dependency-free simulator for a single Tidewatch buoy."""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url: str, method: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def create_buoy(api_url: str, name: str) -> str:
    response = request_json(f"{api_url}/api/v1/buoys", "POST", {"name": name})
    return response["id"]


def build_payload() -> dict:
    measured_at = datetime.now(timezone.utc).isoformat()
    temperature = random.uniform(17.0, 24.0)
    pressure = random.uniform(100.8, 102.2)
    salinity = random.uniform(34.5, 38.0)
    return {
        "temperatures": [
            {"temperature_celsius": round(temperature, 2), "sensor_channel": "A", "measured_at": measured_at},
            {"temperature_celsius": round(temperature + random.uniform(-0.15, 0.15), 2), "sensor_channel": "B", "measured_at": measured_at},
        ],
        "pressures": [
            {"pressure_kpa": round(pressure, 3), "sensor_channel": "A", "measured_at": measured_at},
            {"pressure_kpa": round(pressure + random.uniform(-0.08, 0.08), 3), "sensor_channel": "B", "measured_at": measured_at},
        ],
        "salinity": [
            {"salinity_psu": round(salinity, 2), "sensor_channel": "A", "measured_at": measured_at},
            {"salinity_psu": round(salinity + random.uniform(-0.05, 0.05), 2), "sensor_channel": "B", "measured_at": measured_at},
        ],
        "battery": {"battery_percent": round(random.uniform(70.0, 95.0), 1), "measured_at": measured_at},
    }


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
    print(f"Simulating {buoy_id} against {api_url}")

    while True:
        try:
            result = request_json(
                f"{api_url}/api/v1/buoys/{buoy_id}/telemetry",
                "POST",
                build_payload(),
            )
            print(f"Accepted {result['accepted_readings']} readings")
        except (HTTPError, URLError, TimeoutError) as error:
            print(f"Telemetry send failed: {error}")

        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
