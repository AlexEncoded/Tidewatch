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
coordinates the per-buoy issue snapshot. The remaining large cross-cutting
work is concentrated in telemetry ingestion. HTTP boundaries are isolated so
the use cases can be extracted incrementally and validated by the API and
worker test suites.

The maintenance use case now declares a read-only `MaintenanceReader` input
port composed from the telemetry and battery query ports. `BuoyRepository` is
the current infrastructure adapter; the application service does not need to
know about its SQLAlchemy session.

The physical-device health summary follows the same pattern through the
`DeviceHealthReader` port, keeping heartbeat and status mapping outside the
HTTP adapter.

The SQLAlchemy adapter maps buoy, device and persisted sensor-health entities
to immutable snapshots in `apps/api/app/persistence_mappers.py`. These mapping
functions stay separate from query and transaction orchestration in
`BuoyRepository`, making persistence-to-domain translation directly testable.
Physical-device registration, heartbeat and status operations use a dedicated
`DeviceRepository`. `BuoyRepository` no longer inherits from it; for the
remaining battery-ingestion compatibility methods it composes a device
repository over the same SQLAlchemy session and delegates device lookups and
heartbeats explicitly.
Buoy registration and operational status persistence now use a separate
`BuoyRegistryRepository`, leaving telemetry storage out of those fleet writes.
The same adapter owns buoy enumeration and snapshot mapping; the aggregate
temporarily delegates snapshot enumeration for maintenance composition.
Buoy entity lookup and existence checks also pass through this registry adapter,
including the heartbeat refresh performed after telemetry writes.
Stale-buoy evaluation reads heartbeat fields through a dedicated
`BuoyActivityRepository`; the age and eligibility rules remain in the
application layer.
The fleet overview uses `BuoySummaryRepository`, which composes buoy records
with the telemetry adapter's latest-reading queries instead of placing that
cross-context projection in `BuoyRepository`.
Location history writes and current-coordinate synchronization use a dedicated
`BuoyLocationRepository`; batch ingestion delegates to the same adapter, so
both entry points preserve one persistence path.
Location-history and fleet-wide position queries use that adapter as well;
`BuoyRepository` retains only temporary delegation for compound telemetry and
maintenance gateways.
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

## Servicios Azure

- AKS para ejecutar las cargas de trabajo.
- ACR para almacenar imágenes.
- PostgreSQL Flexible Server para persistencia.
- Key Vault para secretos y certificados.
- Virtual Network y Private Endpoints para conectividad privada.
- Log Analytics, Managed Prometheus y Managed Grafana para observabilidad.
