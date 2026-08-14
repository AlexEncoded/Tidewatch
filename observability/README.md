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
`prometheus/prometheus.yml`, junto con una regla para detectar boyas silenciosas
en `alerts/tidewatch.rules.yml`.

El dashboard inicial de Grafana está en `grafana/dashboards/` y se provisiona
con la configuración de `grafana/provisioning/`.
