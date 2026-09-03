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
La ausencia de una unidad se publica como `tidewatch_redundant_device_missing`
y dispara una alerta crítica tras cinco minutos.
La ausencia de un canal ambiental se publica como
`tidewatch_sensor_channel_missing` con las etiquetas de familia y canal, y
dispara una alerta de mantenimiento tras cinco minutos.

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
