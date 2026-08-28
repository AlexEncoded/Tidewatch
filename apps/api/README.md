# Tidewatch API

Servicio FastAPI de Tidewatch. Registra boyas, ingiere telemetría ambiental,
persiste históricos y expone análisis experimentales, salud redundante y
operación de mantenimiento.

## Ejecutar localmente con PostgreSQL

Desde la raíz del repositorio:

```bash
docker compose up --build
```

La API estará disponible en <http://localhost:8000> y PostgreSQL en el puerto
`5432`.

## Ejecutar solo la API

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Por defecto, la ejecución local usa SQLite (`tidewatch.db`). Para conectar a
PostgreSQL, define `DATABASE_URL` usando el formato de `.env.example`.
En despliegues con Secrets Store CSI, la API también acepta
`DATABASE_URL_FILE` y lee la URL desde el fichero secreto montado.

Las migraciones del esquema se ejecutan con:

```bash
alembic upgrade head
```

El contenedor de la API ejecuta este comando automáticamente antes de arrancar.

El pipeline de CI ejecuta las migraciones contra PostgreSQL antes de lanzar los
tests de la API.

Documentación interactiva: <http://localhost:8000/docs>

Métricas Prometheus: <http://localhost:8000/metrics>

El tracing OpenTelemetry está desactivado por defecto. Para activarlo, define
`OTEL_ENABLED=true` y configura `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` con el
endpoint OTLP HTTP de tu colector. `OTEL_SERVICE_NAME` permite identificar el
servicio en el backend de trazas.

## Endpoints iniciales

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/buoys` | Registrar una boya y su ubicación |
| `GET` | `/api/v1/buoys` | Listar boyas y resumen de última telemetría |
| `GET` | `/api/v1/buoys/stale` | Detectar boyas sin comunicación |
| `PATCH` | `/api/v1/buoys/{id}/status` | Cambiar estado operativo |
| `PATCH` | `/api/v1/buoys/{id}/location` | Actualizar posición |
| `POST` | `/api/v1/buoys/{id}/telemetry` | Ingerir un lote de telemetría |
| `POST` | `/api/v1/buoys/{id}/temperatures` | Registrar temperatura |
| `GET` | `/api/v1/buoys/{id}/temperatures` | Consultar historial |
| `POST` | `/api/v1/buoys/{id}/pressures` | Registrar presión |
| `GET` | `/api/v1/buoys/{id}/pressures` | Consultar presión |
| `GET` | `/api/v1/buoys/{id}/pressure-analysis` | Estimar oleaje experimental |
| `POST` | `/api/v1/buoys/{id}/salinity` | Registrar salinidad |
| `GET` | `/api/v1/buoys/{id}/salinity` | Consultar salinidad |
| `POST` | `/api/v1/buoys/{id}/battery` | Registrar batería A/B |
| `GET` | `/api/v1/buoys/{id}/battery` | Consultar batería, opcionalmente por unidad |
| `GET` | `/api/v1/buoys/{id}/battery/history` | Consultar histórico de batería por unidad |
| `GET` | `/api/v1/buoys/{id}/battery-health` | Comparar batería A/B |
| `GET` | `/api/v1/buoys/{id}/locations` | Consultar histórico de posiciones |
| `GET` | `/api/v1/buoys/{id}/locations/export` | Exportar posiciones de una boya |
| `GET` | `/api/v1/buoys/{id}/movement-analysis` | Analizar movimiento experimental |
| `GET` | `/api/v1/buoys/{id}/wave-analysis` | Fusionar GNSS/IMU para oleaje experimental |
| `POST` | `/api/v1/buoys/{id}/underwater-acoustic` | Registrar intensidad de eco submarino |
| `GET` | `/api/v1/buoys/{id}/underwater-acoustic` | Consultar eco submarino |
| `GET` | `/api/v1/locations/export` | Exportar posiciones de toda la flota |
| `GET` | `/api/v1/buoys/{id}/sensor-health` | Comparar sensores A/B |
| `GET` | `/api/v1/maintenance/issues` | Consultar incidencias |
| `GET` | `/api/v1/buoys/{id}/temperature-analysis` | Analizar anomalías |
| `GET` | `/api/v1/alerts/temperature` | Listar alertas de temperatura |
| `POST` | `/api/v1/alerts/temperature/evaluate` | Persistir anomalías actuales |
| `GET` | `/api/v1/alerts/temperature/stored` | Consultar alertas persistidas |
| `POST` | `/api/v1/alerts/temperature/{id}/resolve` | Resolver una alerta |

Las lecturas aceptan temperaturas entre `-5 °C` y `45 °C`. Las boyas y lecturas
se persisten en PostgreSQL cuando se ejecuta mediante Docker Compose.

Las lecturas ambientales pueden incluir `sensor_id` y `firmware_version` para
conservar la procedencia física y del software de cada canal. Ambos campos son
opcionales para aceptar telemetría de dispositivos anteriores.

La ubicación es opcional en esta fase. Si se proporciona, `latitude` debe estar
entre `-90` y `90`, y `longitude` entre `-180` y `180`.

Cada lectura actualiza `last_seen_at`. El estado operativo puede ser `active`,
`maintenance` o `inactive`.

`/api/v1/buoys/stale` devuelve boyas activas cuya última lectura supera el
`max_age_minutes` indicado. Las boyas en mantenimiento o inactivas no se
consideran silenciosas.

El análisis compara la lectura más reciente con la media de la ventana
solicitada, calcula el cambio entre la primera y la última lectura e identifica
la tendencia como `rising`, `falling` o `stable`. Para marcar anomalías necesita
al menos tres lecturas. El umbral por defecto es `2 °C` y se puede ajustar con
`threshold`.

La API expone métricas Prometheus de lecturas aceptadas, temperatura actual,
última comunicación, movimiento y salud energética A/B.

`/api/v1/buoys/{id}/wave-analysis` combina una ventana de posiciones GNSS con
lecturas IMU y devuelve una estimación experimental. `window` controla el
número máximo de muestras; la calibración con datos reales sigue pendiente.

La acústica submarina acepta intensidades de eco entre `-200` y `100 dB`, con
canales redundantes A/B y persistencia en PostgreSQL.

Cada petición HTTP genera un log de una línea en stdout con método, ruta,
código de estado y duración en milisegundos, preparado para su recolección
centralizada en Kubernetes.
La misma actividad se mide con las métricas Prometheus
`tidewatch_http_requests_total` y `tidewatch_http_request_duration_seconds`.

`/api/v1/buoys/{id}/sensor-health` acepta `max_age_minutes` para distinguir un
canal sin telemetría reciente de uno que todavía está operativo. El mismo
umbral se aplica a la cola de `/api/v1/maintenance/issues`.

`POST /api/v1/buoys/{id}/sensor-health/check` guarda una evaluación con sus
divergencias y canales ausentes. `GET /api/v1/buoys/{id}/sensor-health/history`
permite revisar esas evaluaciones sin recalcularlas.
El campo `decisions` explica qué decisión tomó cada familia ambiental: promedio
de A/B, fallback a un canal disponible o dato inválido.

Para notificar incidencias a un sistema externo, configura
`MAINTENANCE_WEBHOOK_URL` y ejecuta `POST /api/v1/maintenance/notifications`.
La API envía un payload JSON con `source` e `issues` y no expone la URL
configurada en la respuesta.

Las alertas calculadas bajo demanda se pueden persistir explícitamente mediante
`evaluate`. La misma lectura no crea duplicados gracias a la restricción única
por boya y fecha de medición. Las alertas persistidas empiezan en estado `open`
y pueden pasar a `resolved`.

## Tests

```bash
pytest
```
