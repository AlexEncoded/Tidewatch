# Progreso del proyecto

## Punto actual

Tidewatch tiene una plataforma funcional local y una base de infraestructura
Azure preparada. La aplicación mide temperatura, presión, salinidad y batería,
persiste datos en PostgreSQL, estima oleaje, analiza anomalías y genera
incidencias de mantenimiento.

La plataforma ya incluye CI, escaneos de seguridad, Helm, Argo CD, Terraform,
AKS, Key Vault, Prometheus, Grafana, mapa operativo, sensores redundantes A/B,
alertas, logs HTTP a stdout, métricas de tráfico y políticas base de Kubernetes.
La base de Workload Identity está preparada con Terraform y Helm, pero los
recursos Azure con coste todavía no se han desplegado.

## Nueva visión de producto

El objetivo de largo plazo es evolucionar hacia una flota de
“turbomegaboyas”: además de temperatura, presión, salinidad, batería y
posición, incorporarán IMU, luz, viento, corrientes, turbidez, oxígeno disuelto,
pH, conductividad, clorofila-a, meteorología, altimetría acústica y sensores
avanzados de oleaje o acústica submarina. La expansión será incremental y cada
familia deberá quedar integrada en API, base de datos, simulador, CI,
observabilidad y mantenimiento.

La arquitectura funcional será dual: cada boya llevará dos dispositivos físicos
idénticos, A y B, con sensores, batería, procesamiento y comunicaciones propios.
Si una unidad falla, la otra mantendrá la boya operativa. Las dos lecturas se
conservarán para auditoría y se compararán con márgenes específicos; las
divergencias se marcarán como incongruentes o poco fiables y generarán una
incidencia de mantenimiento. La disponibilidad objetivo de la boya será del
99,99%, incluyendo la capacidad de seguir operativa ante el fallo de una de
las unidades.

## Historial de entregas

| Commit | Entrega |
|---|---|
| `d73f344` | Estructura inicial del proyecto |
| `531d5ba` | Persistencia PostgreSQL y Docker Compose |
| `822f297` | Simulador de telemetría |
| `e7234bd` | Migraciones Alembic |
| `01feac2` | Análisis de anomalías |
| `de74696` | Análisis de tendencias |
| `2b1ead7` | Alertas de temperatura |
| `33231b0` | Localización de boyas |
| `b8d256b` | Estado operativo y última comunicación |
| `0180875` | Detección de boyas silenciosas |
| `a8c20d7` | Chart Helm |
| `c44a097` | Aplicación Argo CD para dev |
| `3f42d12` | Fundación Azure dev |
| `4b312a3` | Módulo de red Azure |
| `8f57aa3` | PostgreSQL privado en Azure |
| `9231f7d` | Módulo AKS |
| `37ce6ea` | Módulo Azure Key Vault |
| `ff9a22c` | Métricas Prometheus |
| `ca0a388` | Dashboard Grafana |
| `bf9d8e6` | CI inicial |
| `a020884` | CI contra PostgreSQL |
| `01dad93` | Escaneos DevSecOps |
| `9fb7d74` | Políticas base de Kubernetes |
| `fc6dbf5` | Telemetría de presión |
| `ece3ee5` | Estimación experimental de oleaje |
| `823faf0` | Telemetría de salinidad |
| `316f8ad` | Clasificación del estado del mar |
| `de41958` | Mapa operativo de boyas |
| `40388ac` | Redundancia A/B y salud de sensores |
| `ac6bd10` | Métricas y alertas de observabilidad |
| `8002c76` | Paneles de sensores en Grafana |
| `47be24d` | Resumen de incidencias de mantenimiento |
| `0b5ba30` | Cola de mantenimiento en frontend |
| `d352dfc` | Telemetría de batería |

## Últimos avances

- `b3c13f7`: `sensor_id` y `firmware_version` opcionales en el modelo, API,
  repositorio y migración `0012_sensor_provenance`.
- `b52b3ef`: el simulador emite procedencia estable por familia y canal.
- `f17c550`: canales redundantes obsoletos detectados con `max_age_minutes`.
- `80e24c7`: endpoint de notificaciones mediante webhook genérico.
- `65f4e3d` y `d63a68b`: Workload Identity de API preparado en Terraform y
  Helm; validaciones de Terraform y plataforma en verde.
- `1824948` y `0318dff`: logs y métricas HTTP de baja cardinalidad.
- `cfbf671` y `b7af340`: documentación y métricas de observabilidad.
- `b844655`: historial persistente de evaluaciones de salud de sensores.
- `5e08e3f`: documentación de los endpoints de historial de salud.
- `2b9bcdb`: decisiones de fallback persistentes por familia de sensor.
- `aa7dbb4`: documentación de las decisiones de fallback.
- `f1a6ad0`: métrica Prometheus para la decisión activa por familia.
- `3325476`: documentación de la métrica de decisiones.
- `df291d0` y `0b52eee`: cobertura k6 de evaluación e histórico de salud.
- `945f9db`: panel Grafana de decisiones de salud.
- `ab13952` y `dbe9b16`: alerta y documentación de decisiones inválidas.
- `999ccdb`: alerta de warning para fallback activo de un único canal.
- `7df3c1a`: validación de reglas Prometheus mediante `promtool` en CI.
- `8eec6e6`: validación del JSON del dashboard Grafana en CI.
- `643101e`: persistencia A/B de IMU con aceleración, velocidad angular y
  migración `0015_imu_readings`.
- `10c9703`: endpoints, ingesta por lote, resumen y métricas Prometheus de IMU.
- `d8c2ef0`: simulador y prueba unitaria de telemetría IMU.
- `aea0d6e`: cobertura API de ingesta IMU y métricas.
- `96dcfbd` y `b12dee3`: panel Grafana y documentación de IMU.

La IMU está disponible de extremo a extremo. Su integración A/B está
completada: el historial persiste el delta de aceleración y reutiliza las
decisiones y alertas de salud existentes.
La luz ambiental también está completa de extremo a extremo: lux A/B,
persistencia, API, simulador, diagnóstico, métricas y Grafana. El siguiente
sensor prioritario es anemómetro y veleta.
Anemómetro y veleta ya están completos: velocidad y dirección A/B,
comparación circular en salud, persistencia, API, simulador, tests, métricas y
Grafana. El siguiente bloque prioritario es corrientes marinas.
Las corrientes marinas también están completas con velocidad y dirección A/B,
comparación circular, migraciones, API, simulador, tests y Grafana. El próximo
sensor prioritario es turbidez.
La turbidez también está completa: NTU A/B, persistencia, API, simulador,
diagnóstico, tests, métricas y Grafana. El oxígeno disuelto también está
completo: mg/L A/B, persistencia `0025_dissolved_oxygen_readings`, salud
mediante `0026_dissolved_oxygen_health_delta`, API, simulador, tests, métricas
y Grafana. El pH también está completo: escala 0–14 A/B, persistencia
`0027_ph_readings`, salud mediante `0028_ph_health`, API, simulador, tests,
métricas y Grafana. La conductividad también está completa: µS/cm A/B,
persistencia `0029_conductivity`, salud mediante `0030_conductivity_health`,
API, simulador, tests, métricas y Grafana.
La clorofila-a también está completa: µg/L A/B, persistencia
`0031_chlorophyll`, salud mediante `0032_chlorophyll_health`, API, simulador,
tests, métricas y Grafana.
La lluvia también está completa: mm/h A/B, persistencia `0033_rainfall`, salud
mediante `0034_rain_health`, API, simulador, tests, métricas y Grafana. El
siguiente bloque meteorológico es aire.
La humedad del aire también está completa: porcentaje A/B, persistencia
`0035_humidity`, salud mediante `0036_humidity_health`, API, simulador, tests,
métricas y Grafana. Queda pendiente temperatura del aire y presión atmosférica
dedicada.
La temperatura del aire también está completa: °C A/B, persistencia
`0037_air_temperature`, salud mediante `0038_air_temp_health`, API, simulador,
tests, métricas y Grafana. El siguiente pendiente es presión atmosférica
dedicada.

La presión atmosférica también está completa: kPa A/B, persistencia
`0039_atmospheric_pressure`, salud mediante `0040_atm_pressure_health`, API,
simulador, tests, métricas y Grafana.

La API incorpora tracing OpenTelemetry opcional: permanece desactivado por
defecto y, al activar `OTEL_ENABLED`, instrumenta FastAPI y exporta spans por
OTLP HTTP con nombre de servicio configurable.

Se añadió un experimento de chaos controlado en `chaos/inject_ab_discrepancy.py`
que inyecta una divergencia A/B y verifica la decisión `degraded` de salud.

La suite CI y los escaneos de imágenes pasan. Gitleaks tuvo un fallo
intermitente de infraestructura por `429 Too Many Requests` al descargar la
acción desde `codeload.github.com`; un commit posterior volvió a pasar el
escaneo.

## Próxima sesión

Elegir el siguiente bloque: configurar un colector centralizado para stdout,
incorporar OpenTelemetry, persistir historial de salud/fallback, añadir tests
de carga o preparar un despliegue Azure `dev` controlado. No desplegar recursos
Azure con coste sin revisar presupuesto y aprobación explícita.
