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

## Servicios Azure

- AKS para ejecutar las cargas de trabajo.
- ACR para almacenar imágenes.
- PostgreSQL Flexible Server para persistencia.
- Key Vault para secretos y certificados.
- Virtual Network y Private Endpoints para conectividad privada.
- Log Analytics, Managed Prometheus y Managed Grafana para observabilidad.
