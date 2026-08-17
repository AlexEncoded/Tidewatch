# Tidewatch buoy simulator

Simulador de una boya que genera pequeñas variaciones de temperatura, presión,
salinidad y batería y las envía a la API periódicamente. Cada ciclo usa la
ingestión batch para transmitir los sensores A/B en una sola petición. Es la
primera fuente de telemetría reproducible para desarrollo local y pruebas de
extremo a extremo.

## Configuración

| Variable | Por defecto | Descripción |
|---|---|---|
| `API_URL` | `http://localhost:8000` | URL de la API |
| `BUOY_NAME` | `Mediterranean Sentinel` | Nombre de la boya simulada |
| `INTERVAL_SECONDS` | `10` | Frecuencia de lecturas |
| `BASE_TEMPERATURE_CELSIUS` | `19.5` | Temperatura inicial |
| `BASE_LATITUDE` | `36.7` | Latitud inicial |
| `BASE_LONGITUDE` | `3.1` | Longitud inicial |
| `TELEMETRY_RETRIES` | `3` | Reintentos ante red o errores `5xx` |
| `RETRY_BACKOFF_SECONDS` | `1` | Espera inicial entre reintentos |
| `SENSOR_FIRMWARE_VERSION` | `2.4.1` | Versión emitida para los sensores simulados |

El simulador crea la boya automáticamente si todavía no existe.
Los errores de validación `4xx` no se reintentan; los errores temporales de red
o del servidor usan backoff exponencial.
La posición se desplaza ligeramente en cada ciclo para simular movimiento.
Cada lectura ambiental incluye un `sensor_id` estable por familia y canal, así
como la versión de firmware configurada.

Los tests del worker se ejecutan con `pytest` en GitHub Actions.
