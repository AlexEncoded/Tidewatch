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
