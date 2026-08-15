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

## Servicios Azure

- AKS para ejecutar las cargas de trabajo.
- ACR para almacenar imágenes.
- PostgreSQL Flexible Server para persistencia.
- Key Vault para secretos y certificados.
- Virtual Network y Private Endpoints para conectividad privada.
- Log Analytics, Managed Prometheus y Managed Grafana para observabilidad.
