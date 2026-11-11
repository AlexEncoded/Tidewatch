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

Application services must not import SQLAlchemy sessions, FastAPI objects, or
Pydantic HTTP contracts.
Repository implementations satisfy the protocols structurally, so the use
cases remain testable without PostgreSQL.

Sensor health contracts live in `sensor_health_ports.py`: its reader lists the
supported A/B sensor families and persisted checks, while its writer and
gateway ports persist completed evaluations as domain snapshots. This explicit
query contract prevents passing untyped repositories into the use case.
SQLAlchemy repositories satisfy the contracts structurally; the application
layer does not depend on repository implementations or HTTP response models.

Fleet lifecycle and location contracts live in `fleet_ports.py`, device
contracts in `device_ports.py`, battery telemetry in `battery_ports.py`,
quality summaries in `quality_ports.py`, temperature anomaly and alert
contracts in `alert_ports.py`, and durable telemetry, queueing, metrics, and
unit-of-work contracts in `telemetry_ports.py`.
The composite telemetry ingestion gateway is grouped there alongside its
queueing, transaction, and metrics contracts.
The composite read contract for maintenance evaluation lives in
`maintenance_ports.py` and explicitly composes those contexts.
Cross-context pressure, temperature, and wave analysis contracts, including
wave analysis combining sensor and fleet reads, live in `analysis_ports.py`.
`WaveAnalysisMetrics` is the output port for publishing analysis results; the
Prometheus adapter implements it outside the HTTP route.
Maintenance evaluation exposes its battery and movement metric output through
`MaintenanceMetrics`, also implemented by the Prometheus adapter.
The database liveness/readiness contract lives in `system_ports.py`.
The old generic `ports.py` facade has been removed; each context-specific port
module is now the canonical contract.

Sensor-health reads and persisted-check writes, plus IMU and ambient-light
gateways use `sensor_ports.py`. Wind and marine-current gateways live in
`flow_ports.py`. Water temperature, pressure, and salinity gateways live in
`marine_water_ports.py`;
acoustic altimeter and underwater echo gateways live in
`acoustic_sensor_ports.py`. Turbidity, dissolved oxygen, pH, conductivity, and
chlorophyll-A gateways live in `water_quality_ports.py`; rainfall, humidity,
air temperature, and atmospheric pressure gateways live in `weather_ports.py`.
Cross-sensor health, quality, and analysis contracts live in their
context-specific port modules.

Maintenance notifications expose a `MaintenanceNotificationTransport` input
port as well. The webhook adapter injects the transport from the router, while
payload construction and delivery remain testable without an HTTP client.

Maintenance issue classification is split into application services for sensor
health, reading quality, redundant battery health, and operational state in the
domain. The router coordinates repository reads and metrics, then delegates
issue construction to the maintenance evaluation use case.

`evaluate_maintenance_buoy` coordinates those services for one buoy and
returns both the issue contracts and the values needed by the metrics adapter.
This keeps maintenance orchestration independent from FastAPI and SQLAlchemy.

Device-health summaries load device snapshots through `DeviceHealthReader` and
delegate heartbeat freshness and health mapping to the domain service.

Wave analysis loads IMU and location snapshots through its read port, then
delegates synchronization, estimation, and snapshot construction to the domain.
