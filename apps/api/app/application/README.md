# Application layer

This package contains the application services that coordinate Tidewatch use
cases. Services depend on input ports from `ports.py`, call domain services,
and map domain results to the API response models.

The intended dependency direction is:

```text
HTTP/API adapters -> application services -> domain services
                         ^
                         |
                 persistence input ports
```

Application services must not import SQLAlchemy sessions or FastAPI objects.
Repository implementations satisfy the protocols structurally, so the use
cases remain testable without PostgreSQL.

The sensor-health application service exposes a
`SensorHealthCheckWriter` input port for persisting completed evaluations.
The SQLAlchemy repository is passed in by the API adapter and satisfies this
port structurally; the application layer therefore does not depend on the
repository implementation.

Maintenance notifications expose a `MaintenanceNotificationTransport` input
port as well. The webhook adapter injects the transport from the router, while
payload construction and delivery remain testable without an HTTP client.

Maintenance issue classification is split into application services for sensor
health, reading quality, redundant battery health, and operational state. The
router coordinates repository reads and metrics, then delegates issue
construction to those services.

`evaluate_maintenance_buoy` coordinates those services for one buoy and
returns both the issue contracts and the values needed by the metrics adapter.
This keeps maintenance orchestration independent from FastAPI and SQLAlchemy.
