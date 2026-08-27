# Changelog del proyecto

Registro humano de avances, decisiones relevantes y cambios de enfoque.

## [Unreleased]

- Creada la estructura inicial de planificación.
- Elegido Tidewatch como temática del proyecto.
- Implementado el primer MVP de la API: boyas y lecturas de temperatura del mar.
- Sustituido el almacenamiento en memoria por PostgreSQL mediante SQLAlchemy.
- Añadido Docker Compose para levantar la API junto con PostgreSQL localmente.
- Añadido el roadmap completo de Tidewatch y el registro histórico de entregas.
- Documentada la pausa técnica: validar herramientas y preparar el primer
  despliegue Azure controlado antes de seguir ampliando el producto.
- Añadida la primera señal complementaria: lecturas de presión en kPa para
  preparar el cálculo futuro de altura de ola.
- Añadida salinidad en PSU con migración, API, simulador y tests.
- Añadida estimación experimental de altura de ola y clasificación del estado
  del mar a partir de la variación de presión.
- Añadido mapa operativo y visualización de condiciones oceánicas en el
  frontend.
- Añadida redundancia inicial de sensores A/B para temperatura, presión y
  salinidad, con comparación de salud y tolerancias específicas por sensor.
- Añadidas métricas Prometheus, alertas de sensores degradados y paneles
  Grafana para las nuevas señales.
- Añadida cola de mantenimiento para boyas silenciosas y sensores degradados.
- Añadida telemetría de batería y alerta de carga baja.
- Todos los workflows de CI, seguridad, plataforma y Terraform han quedado
  en verde antes de continuar con nuevas características.
- Aprobada la visión de “turbomegaboyas” y documentada la suite futura de IMU,
  luz, viento, corrientes, turbidez, química marina, meteorología, altimetría
  acústica y sensores avanzados de oleaje/acústica submarina.
- Fijada como requisito la arquitectura dual completa: dos dispositivos físicos
  idénticos por boya, cada uno con sensores y batería propios, con objetivo de
  disponibilidad del 99,99% y clasificación A/B de lecturas divergentes.
- Añadida al TODO la evolución progresiva hacia un monolito modular con DDD
  ligero, límites de dominio y puertos/adaptadores.
- Ampliado el resumen de cada boya con las últimas lecturas A/B de temperatura,
  presión y salinidad, manteniendo los campos históricos orientados al canal A
  por compatibilidad.
- Detectados canales redundantes ausentes, con estado `missing_sensors`, métrica
  Prometheus, incidencia de mantenimiento y alerta específica.
- Añadida una ventana configurable `max_age_minutes` para detectar canales que
  dejan de informar aunque exista histórico antiguo del canal.
- Añadidos `sensor_id` y `firmware_version` opcionales a temperatura, presión y
  salinidad, con migración Alembic `0012_sensor_provenance` y emisión desde el
  simulador.
- Añadida notificación externa genérica mediante `MAINTENANCE_WEBHOOK_URL`,
  con respuestas diferenciadas para configuración ausente y fallo del destino.
- Completada la base de Workload Identity: identidad administrada, credencial
  federada OIDC, permiso `Key Vault Secrets User` y ServiceAccount Helm opcional.
- Añadidos logs HTTP estructurados a stdout y métricas Prometheus de volumen,
  estado y latencia de peticiones.
- Los workflows de CI, seguridad, Terraform y plataforma validaron los cambios
  hasta `d63a68b`; un fallo posterior de Scan repository fue un `HTTP 429` al
  descargar Gitleaks desde GitHub, no un hallazgo del repositorio.
- Persistido el historial de evaluaciones de salud A/B mediante la migración
  `0013_sensor_health_history`, `POST /sensor-health/check` y
  `GET /sensor-health/history`.
- Persistidas las decisiones de fallback por familia mediante la migración
  `0014_health_fallback_decisions`, con valores `average`, `fallback_a`,
  `fallback_b` o `invalid`.
- Expuestas las decisiones activas mediante `tidewatch_sensor_health_decision`
  para observabilidad Prometheus sin sustituir las lecturas originales.
- Ampliado el escenario k6 para persistir evaluaciones de salud y consultar su
  histórico en cada iteración.
- Añadido un panel Grafana para agrupar las decisiones actuales de salud por
  `average`, `fallback_a`, `fallback_b` e `invalid`.
- Añadida alerta crítica `TidewatchSensorDecisionInvalid` para decisiones
  `invalid` mantenidas durante cinco minutos.
- Añadida alerta de warning `TidewatchSensorFallbackActive` para detectar
  `fallback_a` o `fallback_b` activos durante diez minutos.
- Añadido un job CI con `promtool` para validar las reglas Prometheus en cada
  push y pull request.
- Ampliado el job de observabilidad para validar también el JSON del dashboard
  Grafana antes de desplegarlo.
- Iniciada la implementación de IMU con aceleración X/Y/Z y velocidad angular
  X/Y/Z, persistencia A/B mediante `0015_imu_readings`, API, métricas y
  simulador.
- Añadida cobertura de API y un panel Grafana para los vectores IMU. Pendiente
  integrar la IMU en el diagnóstico de salud y sus alertas A/B.
- Integrada la IMU en el diagnóstico A/B con delta vectorial de aceleración,
  historial de salud mediante `0016_imu_health_delta` y prueba de comparación.
- Añadida luz ambiental en lux con persistencia A/B mediante `0017_ambient_light_readings`,
  diagnóstico mediante `0018_ambient_light_health_delta`, API, simulador,
  tests y panel Grafana.
- Añadidos anemómetro y veleta con persistencia `0019_wind_readings`, salud
  mediante `0020_wind_health_delta`, comparación circular de dirección, API,
  simulador, tests y panel Grafana.
- Añadidas corrientes marinas con persistencia `0021_marine_current_readings`,
  salud mediante `0022_marine_current_health_delta`, comparación circular,
  API, simulador, tests y panel Grafana.
- Añadida turbidez en NTU con persistencia `0023_turbidity_readings`, salud
  mediante `0024_turbidity_health_delta`, API, simulador, tests y panel
  Grafana.
- Añadida clorofila-a en µg/L con persistencia `0031_chlorophyll`, salud
  mediante `0032_chlorophyll_health`, API, simulador, tests, métricas y panel
  Grafana.
- Añadida lluvia en mm/h con persistencia `0033_rainfall`, salud mediante
  `0034_rain_health`, API, simulador, tests, métricas y panel Grafana.
- Añadida humedad del aire con persistencia `0035_humidity`, salud mediante
  `0036_humidity_health`, API, simulador, tests, métricas y panel Grafana.
- Añadida temperatura del aire con persistencia `0037_air_temperature`, salud
  mediante `0038_air_temp_health`, API, simulador, tests, métricas y panel
  Grafana.
- Añadido oxígeno disuelto en mg/L con persistencia `0025_dissolved_oxygen_readings`,
  salud mediante `0026_dissolved_oxygen_health_delta`, API, simulador, tests,
  métricas y panel Grafana.
- Añadido pH con persistencia `0027_ph_readings`, salud mediante
  `0028_ph_health`, API, simulador, tests, métricas y panel Grafana.
- Añadida conductividad en µS/cm con persistencia `0029_conductivity`, salud
  mediante `0030_conductivity_health`, API, simulador, tests, métricas y panel
  Grafana.
- Añadida presión atmosférica en kPa con persistencia `0039_atmospheric_pressure`,
  salud mediante `0040_atm_pressure_health`, API, simulador, tests, métricas y
  panel Grafana.
- Añadido tracing OpenTelemetry opcional para la API con exportación OTLP HTTP.
- Añadido experimento controlado de chaos para validar discrepancias de sensores
  redundantes A/B.
- Añadidos helpers PowerShell de backup y restauración PostgreSQL con protección
  contra restauraciones accidentales.
- Añadida integración opcional de Secrets Store CSI para obtener `DATABASE_URL`
  desde Azure Key Vault mediante Workload Identity.
- Ajustado el arranque de la API para leer `DATABASE_URL_FILE` desde el volumen
  CSI y evitar depender de un Secret sincronizado previamente.
- Corregido el nombre por defecto del secreto Key Vault a `database-url`, válido
  para las restricciones de nombres de Azure.
- El chart fuerza ahora la ServiceAccount federada cuando se activa Key Vault
  CSI, evitando un arranque sin identidad para leer secretos.
- Añadido al workflow de plataforma un renderizado CI del chart con Key Vault
  CSI y Workload Identity habilitados usando valores no sensibles.
- Añadido workflow manual para publicar las tres imágenes en ACR mediante Azure
  OIDC y etiquetas inmutables basadas en el SHA del commit.
- Añadido altímetro acústico en metros con persistencia A/B, diagnóstico,
  simulador, tests, métricas y panel Grafana.
- Añadida primera fase GNSS con altitud, velocidad, HDOP y satélites, incluyendo
  métricas, simulador, tests y paneles Grafana.
- Añadido sensor acústico submarino con intensidad de eco A/B, persistencia,
  diagnóstico, API, simulador, tests, métricas y panel Grafana.
