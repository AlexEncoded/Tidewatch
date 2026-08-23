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
- Velocidad y dirección del viento por boya y canal redundante.
- Velocidad y dirección de corrientes marinas por boya y canal redundante.
- Turbidez en NTU por boya y canal redundante.
- Oxígeno disuelto en mg/L por boya y canal redundante.
- pH por boya y canal redundante.
- Conductividad en µS/cm por boya y canal redundante.
- Clorofila-a en µg/L por boya y canal redundante.
- Intensidad de lluvia en mm/h por boya y canal redundante.
- Humedad relativa del aire en porcentaje por boya y canal redundante.
- Temperatura del aire en °C por boya y canal redundante.

La configuración de provisioning espera el dashboard en
`/var/lib/grafana/dashboards/tidewatch`. El datasource Prometheus debe estar
configurado con el nombre usado por la instalación de Grafana.
