# Runbook: boya silenciosa

## Señal

Prometheus dispara `TidewatchBuoySilent` cuando una boya activa no comunica
durante más de 30 minutos. La misma situación aparece en
`/api/v1/maintenance/issues` como `silent_buoy`.

## Diagnóstico

1. Consultar la incidencia y confirmar la boya afectada.
2. Revisar `last_seen_at` y las últimas lecturas de cada sensor.
3. Comprobar si existe discrepancia A/B o batería baja.
4. Revisar logs del worker, API y conectividad de la boya.
5. Confirmar que la boya no está intencionadamente en `maintenance`.

## Acción

- Si la boya está accesible, reiniciar el proceso de adquisición y verificar
  una lectura de ambos canales.
- Si la batería está por debajo del 20 %, abrir intervención de mantenimiento.
- Si solo falla un canal, mantener la boya bajo observación y sustituir el
  sensor degradado.
- No marcar la boya como recuperada hasta observar telemetría válida.

## Verificación

```bash
curl http://localhost:8000/api/v1/maintenance/issues
curl http://localhost:8000/api/v1/buoys/<BUOY_ID>/sensor-health
curl http://localhost:8000/api/v1/buoys/<BUOY_ID>/battery
```

Registrar la causa, duración y acción tomada en un postmortem si el incidente
ha afectado a datos o disponibilidad.
