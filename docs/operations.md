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

Compose also starts `telemetry-queue-worker` from the API image. It polls the
durable PostgreSQL queue and can be disabled in Helm with
`telemetryQueueWorker.enabled=false`. The batch endpoint remains synchronous
when `TELEMETRY_INGESTION_MODE=sync`; Compose and Helm enable queued mode, which
returns `202 Accepted` with a `Location` header. Poll that URL for job status;
the response never includes the stored telemetry payload. To roll back to
synchronous ingestion, set `api.telemetryIngestionMode=sync` in Helm or the
equivalent environment variable in Compose.

Run it from the repository root with:

```bash
python scripts/telemetry_simulator.py
```

Use `--once` for a smoke test or `--buoy-id` to send data to an existing buoy.

## Availability monitoring

Prometheus scrapes the API's `/metrics` endpoint. The
`TidewatchApiTargetUnavailable` alert fires if the `tidewatch-api` scrape target
is down for one minute; investigate API/container health and the Prometheus
target page before interpreting request-based availability rules. The
`tidewatch_buoy_last_seen_timestamp_seconds` and
`tidewatch_device_last_seen_timestamp_seconds` gauges contain Unix timestamps
for the most recently received telemetry, not the device-provided measurement
time. This keeps delayed or replayed readings from making a silent unit appear
available. On API startup, the gauges are restored from the latest timestamps
persisted in the database; a registered unit with no telemetry starts at `0`.

The `tidewatch:buoy_availability_ratio5m` and
`tidewatch:device_availability_ratio5m` recording rules show recent liveness.
Their `*_ratio30d` counterparts measure the 99.99% availability objective over
the trailing 30 days, or over the observed period if Prometheus has collected
the series for less than 30 days. A unit counts as available while its last
receipt is less than 30 seconds old; the 30-day query samples availability at
one-minute resolution. The
`TidewatchBuoyAvailabilityBelowTarget` and
`TidewatchDeviceAvailabilityBelowTarget` alerts fire when the 30-day ratio is
below 99.99% for five minutes. The separate `TidewatchBuoySilent` alert uses a
30-minute silence threshold. Inspect the API `/metrics` output and Prometheus
rule evaluations when investigating these alerts. The dashboard also displays
remaining error budget; a 99.99% objective allows approximately 4.32 minutes of
unavailability in a 30-day window.

For device clock diagnostics, `tidewatch_device_clock_offset_seconds` reports
the newest measurement timestamp minus its API receipt time. The
`TidewatchDeviceClockSkew` alert fires when the absolute offset exceeds two
minutes for five minutes. Delivery delay can contribute to the offset, so check
network and queue behavior before changing the device clock.

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
