# Local operations guide

## Start

From the repository root:

```bash
docker compose up --build
```

Endpoints locales:

- Frontend: <http://localhost:8080>
- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Metrics: <http://localhost:8000/metrics>

The simulator creates the configured buoy and emits channels A/B for the
environmental sensors plus battery readings for devices A and B every ten seconds
using the batch telemetry endpoint. The API also accepts direct battery
readings for device B, as well as two battery readings in the same batch, and
compares both units through `battery-health`. The
simulator sends a small position change so the fleet map and recent track can
be exercised with moving coordinates.

Run it from the repository root with:

```bash
python scripts/telemetry_simulator.py
```

Use `--once` for a smoke test or `--buoy-id` to send data to an existing buoy.

## Availability monitoring

Prometheus scrapes the API's `/metrics` endpoint. The
`tidewatch_buoy_last_seen_timestamp_seconds` and
`tidewatch_device_last_seen_timestamp_seconds` gauges contain Unix timestamps
for the most recently received telemetry, not the device-provided measurement
time. This keeps delayed or replayed readings from making a silent unit appear
available. On API startup, the gauges are restored from the latest timestamps
persisted in the database; a registered unit with no telemetry starts at `0`.

The `tidewatch:buoy_availability_ratio5m` and
`tidewatch:device_availability_ratio5m` recording rules count a unit as
available while its last receipt is less than 30 seconds old. The
`TidewatchBuoyAvailabilityBelowTarget` and
`TidewatchDeviceAvailabilityBelowTarget` alerts fire when that ratio is below
99.99% for five minutes. The separate `TidewatchBuoySilent` alert uses a
30-minute silence threshold. Inspect the API `/metrics` output and Prometheus
rule evaluations when investigating these alerts.

## Useful checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/buoys
curl http://localhost:8000/api/v1/maintenance/issues
```

Run the API tests from the repository root with:

```bash
pytest apps/api/tests
```

## Shutdown and reset

```bash
docker compose down
```

To remove only the local development database volume, verify the target first
and then run `docker compose down -v`. Never use this against a production
environment.
