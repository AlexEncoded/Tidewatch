# API reference

La especificación completa está disponible en Swagger cuando la API está
levantada: <http://localhost:8000/docs>.

## Telemetría

Todas las lecturas incluyen `measured_at`, `sensor_channel` (`A` o `B`) y
`quality` (`good`, `suspect` o `invalid`).

Las lecturas `invalid` se conservan para auditoría, pero no participan en los
análisis de tendencia, oleaje ni generación de alertas.
Tampoco participan en la comparación de salud entre canales A/B; se utiliza la
última lectura no inválida disponible.
La última lectura inválida de una familia de sensores genera además una
incidencia `invalid_reading` en la cola de mantenimiento.
La última lectura sospechosa genera una incidencia `suspect_reading` de
severidad `warning` para revisión preventiva.

| Método | Ruta | Propósito |
|---|---|---|
| `POST` | `/api/v1/buoys` | Registrar una boya |
| `GET` | `/api/v1/buoys` | Resumen de la flota |
| `POST` | `/api/v1/buoys/{id}/temperatures` | Registrar temperatura |
| `GET` | `/api/v1/buoys/{id}/temperatures` | Consultar temperatura por canal |
| `POST` | `/api/v1/buoys/{id}/pressures` | Registrar presión |
| `GET` | `/api/v1/buoys/{id}/pressures` | Consultar presión por canal |
| `GET` | `/api/v1/buoys/{id}/pressure-analysis` | Estimar oleaje y estado del mar |
| `POST` | `/api/v1/buoys/{id}/salinity` | Registrar salinidad |
| `GET` | `/api/v1/buoys/{id}/salinity` | Consultar salinidad por canal |
| `POST` | `/api/v1/buoys/{id}/battery` | Registrar batería |
| `POST` | `/api/v1/buoys/{id}/telemetry` | Ingerir un lote de telemetría no vacío |
| `GET` | `/api/v1/buoys/{id}/battery` | Consultar última batería |
| `GET` | `/api/v1/buoys/{id}/sensor-health` | Comparar canales A/B |
| `GET` | `/api/v1/buoys/{id}/quality-summary` | Resumir calidad acumulada |
| `GET` | `/api/v1/maintenance/issues` | Consultar incidencias |

## Operación

| Método | Ruta | Propósito |
|---|---|---|
| `GET` | `/health` | Health check con acceso a base de datos |
| `GET` | `/metrics` | Métricas Prometheus |
| `GET` | `/api/v1/buoys/stale` | Boyas activas sin comunicación |
| `PATCH` | `/api/v1/buoys/{id}/status` | Cambiar estado operativo |
| `PATCH` | `/api/v1/buoys/{id}/location` | Actualizar coordenadas |
| `GET` | `/api/v1/buoys/{id}/locations` | Consultar histórico de posiciones |

La respuesta de ingestión incluye `accepted_readings` y el desglose
`accepted_by_family` para confirmar cuántas lecturas de cada sensor se han
procesado. El lote puede incluir opcionalmente `location` para actualizar las
coordenadas de la boya en la misma operación. Cada posición se conserva con su
marca temporal para reconstruir desplazamientos.
