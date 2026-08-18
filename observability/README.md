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

El dashboard inicial de Grafana está en `grafana/dashboards/` y se provisiona
con la configuración de `grafana/provisioning/`.
