# Redundancia de sensores

## Idea

Cada boya llevará dos sistemas equivalentes: sensores, adquisición y elementos
necesarios para medir las mismas variables. El objetivo es comparar ambas
lecturas y detectar posibles fallos o mediciones sospechosas.

## Objetivos

- Detectar sensores que dejan de responder.
- Identificar lecturas divergentes entre el sistema A y el sistema B.
- Avisar a mantenimiento antes de confiar en datos incorrectos.
- Mantener trazabilidad de qué sensor produjo cada lectura.
- Permitir que una boya siga operativa aunque falle una de las copias.

## Flujo previsto

```text
Sensor A ─┐
          ├─► comparación y validación ─► lectura aceptada
Sensor B ─┘              │
                         ├─► divergencia alta ─► alerta de mantenimiento
                         └─► sensor sin respuesta ─► alerta de mantenimiento
```

## Modelo de datos futuro

Cada lectura debería incluir, como mínimo:

- `sensor_system`: `A` o `B`.
- `sensor_id` y versión del firmware.
- `measured_at`.
- `value` y unidad.
- Calidad de señal y estado del sensor.

La boya podrá publicar también una lectura agregada con la decisión tomada:

- `accepted_a`
- `accepted_b`
- `average`
- `fallback_a`
- `fallback_b`
- `invalid`

## Reglas iniciales posibles

- Si la diferencia absoluta supera un umbral, crear alerta.
- Si un sistema no informa durante un periodo, marcarlo como degradado.
- Si ambos sensores divergen, conservar ambas lecturas para diagnóstico.
- No ocultar automáticamente el dato original aunque se elija un valor de
  respaldo.

## Relación con el futuro sistema de ML

El modelo deberá conocer la calidad y procedencia de cada dato. Las lecturas
marcadas como divergentes o degradadas no deberían entrar directamente en el
dataset sin una estrategia explícita de limpieza.

## Estado actual

Primera iteración implementada. Las lecturas de temperatura, presión y
salinidad incluyen `sensor_channel` con valores `A` o `B`. Las lecturas
históricas se migran al canal `A` y el simulador genera ambas señales con una
pequeña variación controlada.

La API expone `/api/v1/buoys/{buoy_id}/sensor-health`, compara las últimas
lecturas válidas y usa tolerancias específicas: 0.5 °C, 0.25 kPa y 0.2 PSU.
`max_age_minutes` (30 por defecto) evita considerar operativo un canal que solo
tiene histórico antiguo. Las divergencias y ausencias alimentan métricas
Prometheus, alertas y la cola de mantenimiento.

Las lecturas también conservan opcionalmente `sensor_id` y
`firmware_version`. Los dispositivos antiguos pueden omitirlos; el simulador
los genera con identificadores estables por familia y canal.

Las evaluaciones se pueden persistir explícitamente con
`POST /api/v1/buoys/{buoy_id}/sensor-health/check` y consultar mediante
`GET /api/v1/buoys/{buoy_id}/sensor-health/history`. La consulta normal de
`sensor-health` sigue siendo efímera y no escribe historial.
Cada evaluación guarda `decisions` por familia: `average` cuando A/B son
compatibles, `fallback_a` o `fallback_b` cuando solo queda un canal válido, y
`invalid` cuando no hay una lectura utilizable o existe divergencia grave.
La decisión activa también se publica en
`tidewatch_sensor_health_decision`; solo la serie correspondiente a la decisión
actual tiene valor `1`.

El oxígeno disuelto usa la misma política A/B con tolerancia de 1 mg/L. La
delta se guarda como `dissolved_oxygen_delta_mg_l` en el historial de salud;
por debajo del umbral se selecciona `average` y por encima se marca la familia
como degradada.

El resumen de `/api/v1/buoys` expone además la última lectura independiente de
cada canal ambiental mediante `latest_temperature_a/b`,
`latest_pressure_a/b` y `latest_salinity_a/b`. Esto permite a consumidores y
dashboards inspeccionar A y B sin realizar una consulta adicional.

El pH usa una tolerancia A/B de 0,2 unidades y persiste `ph_delta` en cada
evaluación de salud.

La conductividad usa una tolerancia A/B de 2.000 µS/cm y persiste
`conductivity_delta_us_cm` en cada evaluación de salud.

La clorofila-a usa una tolerancia A/B de 5 µg/L y persiste
`chlorophyll_a_delta_ug_l` en cada evaluación de salud.

La lluvia usa una tolerancia A/B de 20 mm/h y persiste `rainfall_delta_mm_h`
en cada evaluación de salud.

La humedad del aire usa una tolerancia A/B de 5 puntos porcentuales y persiste
`humidity_delta_percent` en cada evaluación de salud.

La presión atmosférica usa una tolerancia A/B de 0,25 kPa y persiste
`atmospheric_pressure_delta_kpa` en cada evaluación de salud.

## Pendiente

- Añadir calidad de señal física más detallada; actualmente existe `quality`
  (`good`, `suspect`, `invalid`) como clasificación de la lectura.
- Persistir las decisiones de fallback junto con una política de selección.
- Añadir deduplicación y reintentos persistentes para notificaciones externas.
