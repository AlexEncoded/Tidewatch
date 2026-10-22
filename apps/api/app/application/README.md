# Application layer

This package contains the application services that coordinate Tidewatch use
cases. Services depend on context-specific input ports and call domain
services. HTTP adapters map application and domain results to response models.

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
`SensorHealthCheckWriter` input port for persisting completed evaluations as
domain snapshots. The SQLAlchemy repository is passed in by the API adapter and
satisfies this port structurally; the application layer therefore does not
depend on the repository implementation or HTTP response models.

Its read side uses the `SensorHealthReader` input port, which lists every
supported redundant A/B sensor family. Storage adapters therefore implement an
explicit query contract instead of being passed as an untyped repository
object.

Fleet lifecycle and location contracts live in `fleet_ports.py`, while durable
telemetry and its metrics/unit-of-work contracts live in `telemetry_ports.py`.
The shared `ports.py` remains a compatibility facade during incremental
migration.

Sensor-health reads and persisted-check writes, plus core temperature,
pressure, salinity, IMU, ambient-light, wind, and current gateway contracts use
`sensor_ports.py`; water-chemistry gateways for turbidity, dissolved oxygen, pH,
conductivity, and chlorophyll-A are grouped there as well. Remaining sensor
families, including weather and acoustic gateways, are grouped there as well.
Battery telemetry reading is also grouped in `sensor_ports.py`.
Sensor quality-summary reads use that module too.
Pressure/temperature analysis and alert persistence contracts are grouped in
the sensor ports as well.

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
