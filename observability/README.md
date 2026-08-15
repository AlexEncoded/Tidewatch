# Azure observability

La observabilidad combinará:

- Azure Monitor y Container Insights para el clúster AKS.
- Managed Prometheus para métricas Prometheus.
- Azure Managed Grafana para dashboards.
- Log Analytics y Loki según la necesidad de logs.
- Alertas de Azure Monitor y alertas propias de Prometheus.

Los dashboards, reglas y alertas deben mantenerse como código siempre que sea
posible.

La API expone `/metrics` y ya existe una configuración inicial en
`prometheus/prometheus.yml`, junto con reglas para detectar boyas silenciosas y
sensores redundantes degradados y lecturas inválidas recientes en
`alerts/tidewatch.rules.yml`. La métrica `tidewatch_reading_quality_total`
permite separar la calidad por boya, familia de sensor y canal.
También publica `tidewatch_buoy_movement_speed_mps` para observar deriva y
alertar cuando supera el umbral experimental configurado.
La salud energética dual se expone con `tidewatch_battery_device_percent` y
`tidewatch_battery_delta_percent`.

El dashboard inicial de Grafana está en `grafana/dashboards/` y se provisiona
con la configuración de `grafana/provisioning/`.
