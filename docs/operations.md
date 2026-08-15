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
environmental sensors plus battery readings every ten seconds.

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
