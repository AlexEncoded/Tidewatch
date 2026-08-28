# Roadmap de Tidewatch

## Fase 1 — MVP de telemetría

- [x] Registrar boyas.
- [x] Registrar temperaturas.
- [x] Persistir datos.
- [x] Simular una boya.
- [x] Analizar tendencias y anomalías.
- [x] Generar y resolver alertas.

## Fase 2 — Operación de la flota

- [x] Ubicación de boyas.
- [x] Estado operativo.
- [x] Última comunicación.
- [x] Detección de boyas silenciosas.
- [x] Frontend y mapa.
- [x] Notificaciones externas de mantenimiento mediante webhook genérico.
- [x] Sensores duplicados A/B iniciales.
- [x] Cola interna de incidencias de mantenimiento.
- [x] Batería y autonomía operativa inicial.
- [x] Procedencia de lecturas con `sensor_id` y `firmware_version`.
- [x] Detección de canales redundantes ausentes y obsoletos.
- [x] Persistencia del historial de salud A/B.
- [x] Persistencia de decisiones de fallback por familia.
- [x] IMU inicial con acelerómetro y giroscopio redundantes A/B, diagnóstico
  de delta vectorial y observabilidad.
- [x] Luz ambiental en lux con canales A/B, diagnóstico de delta y
  observabilidad.
- [x] Anemómetro y veleta con velocidad, dirección circular, diagnóstico A/B
  y observabilidad.
- [x] Corrientes marinas con velocidad, dirección circular, diagnóstico A/B y
  observabilidad.
- [x] Turbidez en NTU con canales A/B, diagnóstico de delta y observabilidad.
- [ ] Modelar dos dispositivos físicos idénticos por boya.
- [ ] Duplicar batería, procesamiento, comunicaciones y reloj por unidad.
- [ ] Extender la validación A/B a toda la suite futura de sensores.
- [ ] Definir márgenes de error por sensor y clasificación de incongruencias.
- [ ] Medir la disponibilidad objetivo del 99,99% por boya y por unidad.
- [x] Incorporar IMU inicial para movimiento e inclinación; la fusión avanzada
  orientada al oleaje queda pendiente.
- [x] Incorporar luz ambiental para ciclo día/noche y tormentas.
- [x] Incorporar anemómetro y veleta.
- [x] Incorporar sensor de corrientes marinas.
- [x] Incorporar turbidez.
- [x] Incorporar oxígeno disuelto con persistencia A/B, API, simulador,
  diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar pH con persistencia A/B, API, simulador, diagnóstico de salud,
  tests y panel Grafana.
- [x] Incorporar conductividad con persistencia A/B, API, simulador,
  diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar clorofila-a con persistencia A/B, API, simulador,
  diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar humedad del aire con persistencia A/B, API, simulador,
  diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar temperatura del aire con persistencia A/B, API, simulador,
  diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar presión atmosférica dedicada con persistencia A/B, API,
  simulador, diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar lluvia con persistencia A/B, API, simulador, diagnóstico de
  salud, tests y panel Grafana.
- [x] Incorporar altímetro acústico con persistencia A/B, API, simulador,
  diagnóstico de salud, tests y panel Grafana.
- [x] Incorporar primera fase GNSS con altitud, velocidad, HDOP y satélites.
- [x] Exponer una primera estimación experimental de oleaje mediante fusión
  GNSS/IMU, métrica y dashboard.
- [ ] Evaluar GNSS/IMU avanzado para oleaje.
- [x] Incorporar sensor acústico submarino en primera fase con intensidad de
  eco A/B; queda abierta la evolución hacia usos acústicos avanzados.

## Fase transversal — Evolución arquitectónica

- [ ] Adoptar progresivamente una arquitectura hexagonal con DDD ligero,
  manteniendo el despliegue como monolito modular mientras los límites aún
  evolucionan.
- [ ] Definir los límites de dominio: `fleet`, `telemetry`, `sensors`,
  `maintenance` y `analytics`.
- [ ] Reorganizar la API como monolito modular por contexto de negocio.
- [ ] Separar modelos de dominio de entidades SQLAlchemy y contratos HTTP.
- [ ] Introducir servicios de aplicación para los casos de uso principales.
- [ ] Definir puertos y adaptadores para persistencia, métricas y mensajería.
- [ ] Añadir tests de dominio independientes de FastAPI y PostgreSQL.
- [ ] Documentar decisiones arquitectónicas y relaciones entre contextos.
- [ ] Evaluar extracción de servicios solo cuando existan límites y necesidades
  operativas claras.

## Fase 3 — Plataforma cloud

- [x] Docker Compose local.
- [x] Terraform para Azure.
- [x] Red privada.
- [x] ACR.
- [x] PostgreSQL Flexible Server privado.
- [x] Módulo AKS.
- [x] Key Vault base.
- [x] Helm y Argo CD.
- [x] Base de Workload Identity para la API (Terraform, OIDC y Helm).
- [x] Integración opcional de Secrets Store CSI en el chart Helm.
- [ ] Despliegue real de `dev`.
- [ ] Staging y producción.

## Fase 4 — Observabilidad y resiliencia

- [x] Métricas Prometheus.
- [x] Dashboard Grafana.
- [x] Alertas de boyas silenciosas.
- [x] Métricas de presión, salinidad y sensores degradados.
- [x] Paneles Grafana para nuevas señales.
- [x] Logs HTTP estructurados a stdout preparados para centralización.
- [x] OpenTelemetry opcional con exportación OTLP HTTP para la API.
- [x] Tests de carga básicos con k6 para ingesta, salud, mantenimiento e
  histórico A/B.
- [x] Primer escenario controlado de chaos engineering para discrepancia A/B.
- [ ] Disaster recovery probado.

## Fase 5 — Datos y predicción

- [ ] Histórico de datos suficiente.
- [ ] Flujo continuo de ventanas recientes.
- [ ] Workers distribuidos.
- [ ] Modelo simulado en CPU.
- [ ] Cómputo GPU bajo demanda en Azure.
- [ ] Versionado de datasets y modelos.
