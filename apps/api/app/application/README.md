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
The maintenance application service evaluates the fleet, publishes those
metrics through the port, and returns domain issues for HTTP or notification
use cases to map independently.
The database liveness/readiness contract lives in `system_ports.py`.
The old generic `ports.py` facade has been removed; each context-specific port
module is now the canonical contract.

Sensor-health reads and persisted-check writes live in `sensor_health_ports.py`.
The persisted sensor-health check use case validates buoy existence, evaluates
the current readings, publishes the evaluation through `SensorHealthMetrics`,
and stores the result through the check gateway.
The non-persisting health query uses the same application evaluation and
metrics flow, without storing a check.
Ambient-light gateways live in `ambient_light_ports.py`; IMU gateways live in
`motion_ports.py`; wind and
marine-current gateways live in
`flow_ports.py`. Water temperature, pressure, and salinity gateways live in
`marine_water_ports.py`;
acoustic altimeter and underwater echo gateways live in
`acoustic_sensor_ports.py`. Turbidity, dissolved oxygen, pH, conductivity, and
chlorophyll-A gateways live in `water_quality_ports.py`; rainfall, humidity,
air temperature, and atmospheric pressure gateways live in `weather_ports.py`.
Cross-sensor health, quality, and analysis contracts live in their
context-specific port modules.

Maintenance notifications expose a `MaintenanceNotificationTransport` input
port and a durable job-store port. The application service builds the stable
payload, applies idempotency, and queues the job from domain issues; HTTP maps
idempotency conflicts at the route boundary and the worker uses the injected
transport to deliver notifications.

Maintenance issue classification is split into application services for sensor
health, reading quality, redundant battery health, and operational state in the
domain. The maintenance evaluation use case coordinates repository reads,
publishes metrics through its output port, and returns domain issues for the
route to map to HTTP.

`evaluate_maintenance_buoy` coordinates those services for one buoy and
returns both the issue contracts and the values needed by the metrics adapter.
This keeps maintenance orchestration independent from FastAPI and SQLAlchemy.

The ambient-light ingestion use case checks buoy existence, persists the
domain snapshot, and publishes heartbeat and sensor metrics through ports.
IMU ingestion follows the same boundary and also publishes each acceleration
and angular-velocity axis through the telemetry metrics port.
Water-temperature ingestion now uses the same application boundary for buoy
validation, persistence, heartbeat updates, and sensor metrics.
Water-pressure ingestion follows that boundary for its validation, persistence,
heartbeat, and sensor metrics as well.
Salinity ingestion follows the same application boundary and telemetry ports.
Turbidity ingestion also coordinates buoy validation, persistence, heartbeat,
and sensor metrics through the application layer.
Dissolved-oxygen ingestion now follows this same application boundary.
pH ingestion also delegates buoy validation, persistence, heartbeat, and
sensor metrics to its application use case.
Conductivity ingestion follows this boundary as well.
Chlorophyll-a ingestion uses the same application orchestration pattern.
Rainfall ingestion also delegates persistence and telemetry metrics through
its application use case.
Humidity ingestion uses the same application boundary.
Air-temperature ingestion follows the same pattern through the weather port.
Atmospheric-pressure ingestion also uses its weather application gateway.
Wind ingestion now coordinates buoy validation, persistence, heartbeat, and
both wind metrics through its application use case.
Marine-current ingestion follows the same boundary and publishes its speed
and direction metrics through the metrics port.
Acoustic-altimeter ingestion now uses its application gateway for persistence
and depth metrics.
Underwater-acoustic ingestion follows the same application boundary and
publishes echo-intensity metrics through the telemetry port.
Battery ingestion coordinates buoy and physical-device validation, persistence,
device heartbeat, and battery metrics through its application ports.

Device-health summaries load device snapshots through `DeviceHealthReader` and
delegate heartbeat freshness and health mapping to the domain service.

Wave analysis loads IMU and location snapshots through its read port, then
delegates synchronization, estimation, and snapshot construction to the domain.
