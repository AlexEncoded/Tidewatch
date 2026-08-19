# Grafana dashboards

Dashboards versionados como JSON para Azure Managed Grafana o una instalación
autogestionada.

El dashboard `tidewatch-overview.json` muestra:

- Número total de lecturas aceptadas.
- Temperatura actual por boya.
- Boyas silenciosas.
- Tiempo desde la última lectura.
- Tasa de lecturas por calidad (`good`, `suspect` e `invalid`).
- Nivel de batería por boya.
- Vectores de aceleración y velocidad angular de la IMU por boya, canal y eje.
- Iluminancia ambiental en lux por boya y canal redundante.

La configuración de provisioning espera el dashboard en
`/var/lib/grafana/dashboards/tidewatch`. El datasource Prometheus debe estar
configurado con el nombre usado por la instalación de Grafana.
