"""Controlled local chaos experiment for redundant temperature sensors."""

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def post(base_url: str, path: str, payload: dict) -> dict:
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--difference", type=float, default=10.0)
    args = parser.parse_args()

    try:
        buoy = post(args.api_url, "/api/v1/buoys", {"name": "Chaos A/B experiment"})
        buoy_id = buoy["id"]
        for channel, value in (("A", 20.0), ("B", 20.0 + args.difference)):
            post(
                args.api_url,
                f"/api/v1/buoys/{buoy_id}/temperatures",
                {"temperature_celsius": value, "sensor_channel": channel},
            )
        health = post(args.api_url, f"/api/v1/buoys/{buoy_id}/sensor-health/check", {})
    except (HTTPError, OSError, KeyError) as error:
        print(f"Chaos experiment failed to execute: {error}", file=sys.stderr)
        return 1

    decision = health.get("decisions", {}).get("temperature")
    print(json.dumps({"buoy_id": buoy_id, "decision": decision, "health": health}))
    return 0 if decision == "degraded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
