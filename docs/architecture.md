# Tidewatch architecture

Documentación pública de la arquitectura de Tidewatch en Azure.

La planificación privada y las notas del proceso se mantienen en `PLANNING/`.

## Flujo principal

```text
GitHub Actions
    ↓
Azure Container Registry
    ↓
Argo CD
    ↓
Azure Kubernetes Service
    ├── frontend
    ├── api
    └── worker
        ↓
Azure Database for PostgreSQL
        ↓
Azure Monitor / Log Analytics / Managed Grafana
```

## Flujo de telemetría

```text
Buoy simulator / buoy device
        │ temperature · pressure · salinity · battery · position
        │ sensor channels A/B + battery device A/B + quality metadata
        ▼
FastAPI ingestion API
        ├── PostgreSQL + Alembic migrations
        ├── anomaly and wave estimation
        ├── movement analysis, battery health and maintenance issues
        └── Prometheus metrics
```

The frontend consumes the API, displays fleet locations, recent tracks, ocean
conditions, battery health and the maintenance queue. It also links to a CSV
snapshot export for offline analysis. Pressure-based wave height, movement and
sea-state classification are explicitly experimental until real sensor
calibration is available.

## API adapter boundaries

The FastAPI application is a modular monolith. HTTP adapters are progressively
grouped by responsibility under `apps/api/app/routers/`:

- `devices.py` and `buoys.py` expose fleet and device management;
- `sensors.py` exposes the individual sensor reading contracts and sensor-health
  history;
- `analytics.py`, `battery.py`, `quality.py` and `alerts.py` expose analytical
  and operational use cases;
- `telemetry.py` exposes fleet telemetry exports and `ingestion.py` handles
  batch telemetry ingestion;
- `maintenance.py` exposes maintenance issues and webhook notifications;
- `system.py` exposes health and Prometheus endpoints.

Domain rules remain in `apps/api/app/domain/`, while application services in
`apps/api/app/application/` coordinate use cases and ports. Maintenance
notifications use an application transport port, and `maintenance_evaluation`
coordinates the per-buoy issue snapshot. HTTP boundaries and persistence
adapters are isolated so use cases can be evolved and validated by the API and
worker test suites.

The maintenance use case declares a read-only `MaintenanceReader` input port.
`MaintenanceRepository` composes its dedicated sources; the application service
does not need to know about the SQLAlchemy session.

The physical-device health summary follows the same pattern through the
`DeviceHealthReader` port, keeping heartbeat and status mapping outside the
HTTP adapter.

The SQLAlchemy adapter maps buoy, device and persisted sensor-health entities
to immutable snapshots in `apps/api/app/persistence_mappers.py`. These mapping
functions stay separate from query and transaction orchestration in
the focused SQLAlchemy adapters, making persistence-to-domain translation
directly testable.
Fleet identity and physical-device ORM entities are grouped in
`apps/api/app/fleet_entities.py`; sensor and telemetry mappings remain in the
shared entities module while they are separated incrementally by context.
Physical-device registration, heartbeat and status operations use a dedicated
`DeviceRepository`.
Battery persistence and history queries use `BatteryRepository`, which composes
the device adapter for the battery-ingestion port.
Sensor-health history and check persistence use `SensorHealthRepository`,
which composes the dedicated sensor adapters behind the health ports.
Quality summaries use `QualitySummaryRepository` to aggregate quality labels
across every sensor family that records a quality value.
Fleet overview summaries now compose `BuoyRegistryRepository` with the
dedicated telemetry adapters instead of using the legacy aggregate.
Wave analysis uses `WaveAnalysisRepository` to combine IMU and location
history through their dedicated adapters.
Batch telemetry ingestion now composes fleet, battery, location and per-sensor
adapters through `TelemetryIngestionRepository` rather than the legacy aggregate.
The maintenance reader similarly uses `MaintenanceRepository` to combine
health histories, device state, battery records, location and buoy snapshots.
Buoy registration and operational status persistence now use a separate
`BuoyRegistryRepository`, leaving telemetry storage out of those fleet writes.
The same adapter owns buoy enumeration and snapshot mapping.
Buoy entity lookup and existence checks also pass through this registry adapter,
including the heartbeat refresh performed after telemetry writes.
Stale-buoy evaluation reads heartbeat fields through a dedicated
`BuoyActivityRepository`; the age and eligibility rules remain in the
application layer.
The fleet overview uses `BuoySummaryRepository` to compose buoy records with
the latest telemetry readings across every sensor family, including both
acoustic sensors and their A/B channels.
Location history writes and current-coordinate synchronization use a dedicated
`BuoyLocationRepository`; batch ingestion delegates to the same adapter, so
both entry points preserve one persistence path.
Location-history and fleet-wide position queries use that adapter as well.
The former aggregate repository compatibility facade has been removed;
callers use the focused adapters and application ports directly.
Temperature anomaly persistence and the buoy identity query used for fleet-wide
analysis now live in `TemperatureAlertRepository`, which composes the existing
temperature-reading adapter.
Temperature persistence and reading queries use `TemperatureRepository`; batch
ingestion, maintenance and alert analysis retain narrow delegation while their
composite ports are migrated.
Water-pressure persistence and analysis queries now use `PressureRepository`,
which refreshes buoy activity through the fleet registry adapter.
Salinity persistence and history queries follow the same port/adaptor boundary
through `SalinityRepository`.
IMU persistence and history queries use `ImuRepository`; the wave-analysis
compatibility facade composes it with the location adapter.
Ambient-light persistence and history queries now use `AmbientLightRepository`.
Wind speed and direction persistence and history queries use `WindRepository`.
Marine-current speed and direction persistence and queries use
`MarineCurrentRepository`.
Turbidity persistence and history queries use `TurbidityRepository`.
Dissolved-oxygen persistence and history queries use `DissolvedOxygenRepository`.
pH persistence and history queries use `PHRepository`.
Conductivity persistence and history queries use `ConductivityRepository`.
Chlorophyll-a persistence and history queries use `ChlorophyllARepository`.
Rainfall persistence and history queries use `RainfallRepository`.
Humidity persistence and history queries use `HumidityRepository`.
Air-temperature persistence and history queries use `AirTemperatureRepository`.
Atmospheric-pressure persistence and history queries use
`AtmosphericPressureRepository`.
Acoustic-altimeter persistence and history queries use
`AcousticAltimeterRepository`.
Underwater-acoustic persistence and history queries use
`UnderwaterAcousticRepository`.

## Bounded contexts

The current modular-monolith boundaries are:

| Context | Main responsibility | Current HTTP adapters |
|---|---|---|
| `fleet` | Buoys, physical devices and operational identity | `devices.py`, `buoys.py` |
| `telemetry` | Batch ingestion, provenance and historical exports | `ingestion.py`, `telemetry.py` |
| `sensors` | Sensor readings, redundancy and health decisions | `sensors.py` |
| `maintenance` | Incidents, drift, battery degradation and notifications | `maintenance.py` |
| `analytics` | Quality, battery, alerts, movement and wave estimates | `analytics.py`, `battery.py`, `quality.py`, `alerts.py` |

These are domain boundaries inside one deployment, not independently deployed
services. The application layer is the seam for extracting a use case later;
the decision to split a service remains dependent on operational evidence.

## Durable asynchronous telemetry ingestion

Batch ingestion supports synchronous `200 OK` and durable asynchronous
`202 Accepted` modes. Set `TELEMETRY_INGESTION_MODE=queued` to persist the
validated request as a PostgreSQL job before returning its identifier and a
`Location` header; the default remains synchronous for compatibility. Clients
can retrieve job state from the returned `/api/v1/telemetry/jobs/{job_id}` URL.
The status response does not expose the submitted payload or raw exception
details.

PostgreSQL is the queue source of truth, so no separate broker is required at
the current scale. The queue worker claims jobs with row-level locking and
leases, retries transient failures with bounded backoff, and records terminal
failures for inspection. An optional idempotency key makes repeated submissions
safe. A job's telemetry writes and completion are committed atomically, so a
retry cannot leave a partially persisted batch. Docker Compose and Helm include
the queue worker deployment; production use still requires validating the
deployment and database capacity in the target environment.

## Servicios Azure

- AKS para ejecutar las cargas de trabajo.
- ACR para almacenar imágenes.
- PostgreSQL Flexible Server para persistencia.
- Key Vault para secretos y certificados.
- Virtual Network y Private Endpoints para conectividad privada.
- Log Analytics, Managed Prometheus y Managed Grafana para observabilidad.
