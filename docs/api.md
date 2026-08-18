# API reference

La especificación completa está disponible en Swagger cuando la API está
levantada: <http://localhost:8000/docs>.

## Telemetría

Las lecturas ambientales de temperatura, presión y salinidad incluyen
`measured_at`, `sensor_channel` (`A` o `B`), `sensor_id`,
`firmware_version` y `quality` (`good`, `suspect` o `invalid`).
`sensor_id` y `firmware_version` son opcionales para conservar compatibilidad
con dispositivos antiguos. Las lecturas de batería usan `device_id` (`A` o
`B`) y las posiciones usan `measured_at`.

Las lecturas `invalid` se conservan para auditoría, pero no participan en los
análisis de tendencia, oleaje ni generación de alertas.
Tampoco participan en la comparación de salud entre canales A/B; se utiliza la
última lectura no inválida disponible. Esta regla aplica a las familias
ambientales con `sensor_channel`, no a la batería, que tiene su propia
comparación por `device_id`.
La última lectura inválida de una familia de sensores genera además una
incidencia `invalid_reading` en la cola de mantenimiento.
La última lectura sospechosa genera una incidencia `suspect_reading` de
severidad `warning` para revisión preventiva.
Si una familia ambiental solo recibe datos de uno de sus canales, la salud
devuelve `missing_sensors` con el formato `familia:canal` y mantenimiento crea
una incidencia `missing_sensor_channel`.

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
| `GET` | `/api/v1/buoys/{id}/battery` | Consultar última batería (`device_id` opcional) |
| `GET` | `/api/v1/buoys/{id}/battery/history` | Consultar histórico de batería por unidad |
| `GET` | `/api/v1/buoys/{id}/battery-analysis` | Estimar descarga y autonomía por unidad |
| `GET` | `/api/v1/buoys/{id}/battery-health` | Comparar baterías A/B |
| `GET` | `/api/v1/buoys/{id}/sensor-health` | Comparar canales A/B |
| `POST` | `/api/v1/buoys/{id}/sensor-health/check` | Evaluar y persistir salud A/B |
| `GET` | `/api/v1/buoys/{id}/sensor-health/history` | Consultar histórico de salud |
| `GET` | `/api/v1/buoys/{id}/quality-summary` | Resumir calidad acumulada |
| `GET` | `/api/v1/maintenance/issues` | Consultar incidencias, incluida deriva |
| `POST` | `/api/v1/maintenance/notifications` | Enviar incidencias al webhook configurado |
| `GET` | `/api/v1/alerts/temperature` | Consultar anomalías de temperatura |
| `POST` | `/api/v1/alerts/temperature/evaluate` | Persistir anomalías actuales |
| `GET` | `/api/v1/alerts/temperature/stored` | Consultar alertas persistidas |
| `POST` | `/api/v1/alerts/temperature/{id}/resolve` | Resolver una alerta |

## Operación

| Método | Ruta | Propósito |
|---|---|---|
| `GET` | `/health` | Health check con acceso a base de datos |
| `GET` | `/metrics` | Métricas Prometheus |
| `GET` | `/api/v1/buoys/stale` | Boyas activas sin comunicación |
| `PATCH` | `/api/v1/buoys/{id}/status` | Cambiar estado operativo |
| `PATCH` | `/api/v1/buoys/{id}/location` | Actualizar coordenadas |
| `GET` | `/api/v1/buoys/{id}/locations` | Consultar histórico de posiciones (`limit`, `since`, `until`) |
| `GET` | `/api/v1/buoys/{id}/locations/export` | Exportar posiciones a CSV |
| `GET` | `/api/v1/locations/export` | Exportar posiciones de toda la flota a CSV |
| `GET` | `/api/v1/buoys/{id}/movement-analysis` | Estimar distancia y deriva |

La respuesta de ingestión incluye `accepted_readings` y el desglose
`accepted_by_family` para confirmar cuántas lecturas de cada sensor se han
procesado. El lote puede incluir opcionalmente `location` para actualizar las
coordenadas de la boya en la misma operación. También puede incluir hasta dos
objetos `battery`, uno por `device_id` A/B; el formato antiguo de un único
objeto sigue siendo compatible. Un lote no puede repetir el mismo
`device_id` ni el mismo `sensor_channel` dentro de una familia ambiental.
Cada posición se conserva con su marca temporal para reconstruir
desplazamientos.

`/api/v1/maintenance/issues` acepta `drift_speed_mps` para configurar el límite
de velocidad media que dispara la incidencia `drift_detected`.

`/api/v1/maintenance/notifications` usa `MAINTENANCE_WEBHOOK_URL` para enviar
el listado actual de incidencias como JSON. Devuelve `503` si no hay webhook
configurado y `502` si el destino rechaza o no recibe la petición.

La salud energética se consulta con `battery-health?threshold=10`. Si ambas
unidades están disponibles, devuelve los porcentajes A/B, su diferencia y la
unidad sospechosa cuando supera el umbral. El endpoint de batería acepta
`device_id=A|B`; los registros antiguos se consideran de la unidad A por
compatibilidad. Las incidencias de batería baja identifican explícitamente la
unidad física afectada. Si solo una unidad aporta datos, mantenimiento recibe
la incidencia `missing_redundant_device` para la unidad ausente.

La salud de sensores se consulta con `/sensor-health`. La métrica
`tidewatch_sensor_channel_missing` identifica la familia y el canal sin
telemetría reciente; una ausencia se mantiene separada de una divergencia
entre lecturas disponibles. El parámetro `max_age_minutes` (30 por defecto)
define cuánto tiempo puede tener una lectura antes de considerarse ausente.
La evaluación persistente se solicita con `POST /sensor-health/check`; el
histórico se consulta con `GET /sensor-health/history?limit=50`.
Cada evaluación guarda también la decisión por familia: `average`,
`fallback_a`, `fallback_b` o `invalid`.

El resumen de cada boya también incluye las lecturas redundantes más recientes
como `latest_temperature_a`/`latest_temperature_b`,
`latest_pressure_a`/`latest_pressure_b` y `latest_salinity_a`/
`latest_salinity_b`. Los campos sin lectura son `null`; los campos históricos
`latest_temperature`, `latest_pressure` y `latest_salinity` siguen representando
el canal A para mantener la compatibilidad.
