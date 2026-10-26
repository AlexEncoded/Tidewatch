# Azure observability

La observabilidad combinará:

- Azure Monitor y Container Insights para el clúster AKS.
- Managed Prometheus para métricas Prometheus.
- Azure Managed Grafana para dashboards.
- Log Analytics y Loki según la necesidad de logs.
- Alertas de Azure Monitor y alertas propias de Prometheus.

Los dashboards, reglas y alertas deben mantenerse como código siempre que sea
posible.

La API emite una línea por petición a stdout con `method`, `path`, `status_code`
y `duration_ms`. El colector del entorno debe recoger stdout del contenedor y
añadir las etiquetas de pod, namespace y entorno; la aplicación no escribe
logs en disco.
También expone `tidewatch_http_requests_total` y
`tidewatch_http_request_duration_seconds`, con etiquetas de baja cardinalidad
para método y estado HTTP, para construir paneles de tasa y latencia.
Las decisiones de fallback quedan disponibles en el histórico de salud para
auditoría y no sustituyen las lecturas originales.
La métrica `tidewatch_sensor_health_decision` publica la decisión actual por
familia y boya con valor `1` solo para la decisión activa.
La regla `TidewatchSensorDecisionInvalid` eleva a crítica una decisión
`invalid` mantenida durante cinco minutos.
La regla `TidewatchSensorFallbackActive` eleva un warning cuando una familia
opera durante diez minutos con `fallback_a` o `fallback_b`; sirve para
planificar mantenimiento antes de perder ambos canales.
La IMU publica sus componentes de aceleración y velocidad angular por eje, y
el diagnóstico A/B compara la magnitud del delta de aceleración en
`imu_acceleration_delta_mps2`.

La API expone `/metrics` y ya existe una configuración inicial en
`prometheus/prometheus.yml`, junto con reglas para detectar boyas silenciosas y
sensores redundantes degradados y lecturas inválidas recientes en
`alerts/tidewatch.rules.yml`. La métrica `tidewatch_reading_quality_total`
permite separar la calidad por boya, familia de sensor y canal.
También publica `tidewatch_buoy_movement_speed_mps` para observar deriva y
alertar cuando supera el umbral experimental configurado.
La salud energética dual se expone con `tidewatch_battery_device_percent` y
`tidewatch_battery_delta_percent`.

Las reglas de disponibilidad mantienen el SLO mensual del 99,99% y también
evalúan burn rate rápido: una boya o dispositivo dispara una alerta warning
cuando su disponibilidad cae por debajo de 99,85% tanto en cinco minutos como
en una hora, sostenida durante dos minutos. Esta alerta temprana complementa
la alerta de incumplimiento del objetivo mensual; los umbrales deben revisarse
con datos de operación reales.
La ausencia de una unidad se publica como `tidewatch_redundant_device_missing`
y dispara una alerta crítica tras cinco minutos.
`tidewatch_device_clock_offset_seconds` compara la marca de tiempo de la última
medición de la unidad con la hora de recepción de la API. La alerta
`TidewatchDeviceClockSkew` avisa si la diferencia absoluta supera dos minutos
durante cinco minutos; una entrega retrasada también puede contribuir a esa
diferencia, por lo que conviene revisar la conectividad junto con la
sincronización del reloj.
Cada lote puede incluir `device_runtime` con porcentajes de CPU y memoria por
unidad. Las métricas `tidewatch_device_cpu_usage_percent` y
`tidewatch_device_memory_usage_percent` alimentan el dashboard y las alertas
warning `TidewatchDeviceHighCpu` y `TidewatchDeviceHighMemory` cuando el uso
supera 90% durante cinco minutos.
Los campos opcionales de comunicación permiten publicar pérdida de paquetes y
latencia round-trip por unidad. `TidewatchDevicePacketLoss` alerta por encima
del 5% y `TidewatchDeviceHighNetworkLatency` por encima de 2.000 ms durante
cinco minutos; son umbrales iniciales que deben ajustarse al enlace desplegado.
También se aceptan RSSI (`tidewatch_device_signal_strength_dbm`) y relación
señal/ruido (`tidewatch_device_signal_to_noise_ratio_db`) por unidad física.
Se publican para diagnóstico; los umbrales dependen de la tecnología y el
enlace desplegado.
La cola durable publica en `/metrics` los jobs por estado,
`tidewatch_telemetry_ingestion_oldest_pending_seconds`, leases vencidos, jobs
reintentados y suma de intentos. Se refrescan desde PostgreSQL en cada scrape
y no usan identificadores de job como etiquetas. Las alertas
`TidewatchTelemetryQueueBacklog`, `TidewatchTelemetryQueueOldestJob`,
`TidewatchTelemetryQueueExpiredLease`,
`TidewatchTelemetryQueueRetryingJobs` y
`TidewatchTelemetryQueueTerminalFailures` detectan congestión y fallos; el
dashboard incluye paneles de profundidad y antigüedad de la cola.
La ausencia de un canal ambiental se publica como
`tidewatch_sensor_channel_missing` con las etiquetas de familia y canal, y
dispara una alerta de mantenimiento tras cinco minutos.
La disponibilidad de la API se publica como la recording rule
`tidewatch:api_availability_ratio5m`, calculada a partir de
`tidewatch_http_requests_total` y protegida contra divisiones por cero. La
alerta `TidewatchApiServerErrors` avisa cuando esa disponibilidad cae por
debajo del 99% durante cinco minutos; el panel de errores 5xx reutiliza la
misma serie para mantener una única definición operativa.
`TidewatchApiTargetUnavailable` detecta aparte que Prometheus no pueda scrapear
el endpoint `/metrics`, un caso en el que las métricas basadas en peticiones
dejan de estar disponibles.
La disponibilidad objetivo del 99,99% por boya y unidad física sigue pendiente
de validación completa en un entorno desplegado. Las recording rules
`tidewatch:buoy_availability_ratio5m` y
`tidewatch:device_availability_ratio5m` sirven para investigar cortes recientes;
las variantes `*_ratio30d` miden el objetivo de disponibilidad sobre los últimos
30 días (o desde la primera muestra de Prometheus si la serie es más reciente).
La ventana de 30 días se evalúa con una resolución de un minuto.
Se considera disponible si el último heartbeat tiene menos de 30 segundos
(tres intervalos esperados de telemetría de 10 segundos).
Las series se restauran desde las unidades registradas al arrancar la API y las
unidades nuevas se publican desde su registro; una unidad sin ningún heartbeat
parte de timestamp cero y cuenta como no disponible.
`TidewatchBuoyAvailabilityBelowTarget` y
`TidewatchDeviceAvailabilityBelowTarget` alertan cuando la proporción 30d cae
por debajo del 99,99%. El dashboard conserva ambas ventanas, 5m y 30d. La
disponibilidad del 99,99% equivale a un presupuesto de 4,32 minutos en 30 días;
los paneles de error budget muestran qué porcentaje de ese margen queda. La
correlación con RPO/RTO sigue pendiente de pruebas de despliegue.

La humedad del aire se observa con `tidewatch_current_humidity_percent` y su
delta A/B queda registrada como `humidity_delta_percent`.
La temperatura del aire se observa con `tidewatch_current_air_temperature_celsius`
y su delta A/B queda registrada como `air_temperature_delta_celsius`.
La presión atmosférica se observa con `tidewatch_current_atmospheric_pressure_kpa`
y su delta A/B queda registrada como `atmospheric_pressure_delta_kpa`.
El altímetro acústico se observa con
`tidewatch_current_acoustic_altimeter_depth_meters` y su delta A/B queda
registrada como `acoustic_altimeter_delta_meters`.
La primera fase GNSS se observa con `tidewatch_current_gnss_altitude_meters`,
`tidewatch_current_gnss_speed_mps`, `tidewatch_current_gnss_hdop` y
`tidewatch_current_gnss_satellites` por boya.
El sensor acústico submarino se observa con
`tidewatch_current_underwater_acoustic_echo_intensity_db` por boya y canal.
Su diagnóstico A/B calcula `underwater_acoustic_delta_db` y considera degradada
la familia cuando la diferencia supera 5 dB.
La estimación experimental de oleaje se expone como
`tidewatch_current_estimated_wave_height_m` por boya; combina el rango vertical
GNSS con la variabilidad de aceleración vertical de la IMU.
The same flow exposes `tidewatch_current_estimated_wave_period_seconds` per
buoy for the experimental period estimate; it should be validated against
calibrated field data before operational decisions.
La regla `TidewatchExperimentalWaveHigh` genera un warning si supera 2 m
durante diez minutos, únicamente para revisión y validación de calibración.

El dashboard inicial de Grafana está en `grafana/dashboards/` y se provisiona
con la configuración de `grafana/provisioning/`.

Las reglas Prometheus se validan en CI con `promtool` usando la imagen oficial
de Prometheus fijada en `prom/prometheus:v2.55.1`.

La lluvia se observa con `tidewatch_current_rainfall_mm_h` y su delta A/B queda
registrada como `rainfall_delta_mm_h` en el historial de salud.

El oxígeno disuelto se observa con `tidewatch_current_dissolved_oxygen_mg_l`
por boya y canal, y su consistencia redundante queda registrada en
`dissolved_oxygen_delta_mg_l`.
El pH se observa con `tidewatch_current_ph` y su delta A/B queda registrada
como `ph_delta`; la conductividad usa `tidewatch_current_conductivity_us_cm` y
`conductivity_delta_us_cm` para el histórico redundante.
La clorofila-a se observa con `tidewatch_current_chlorophyll_a_ug_l` y su
delta A/B queda registrada como `chlorophyll_a_delta_ug_l`.
El pH se observa con `tidewatch_current_ph` por boya y canal, y su delta A/B
queda registrada como `ph_delta` en el historial de salud.
