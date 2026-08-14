# Tidewatch buoy simulator

Simulador de una boya que genera pequeñas variaciones de temperatura y las
envía a la API periódicamente. Es la primera fuente de telemetría reproducible
para desarrollo local y pruebas de extremo a extremo.

## Configuración

| Variable | Por defecto | Descripción |
|---|---|---|
| `API_URL` | `http://localhost:8000` | URL de la API |
| `BUOY_NAME` | `Mediterranean Sentinel` | Nombre de la boya simulada |
| `INTERVAL_SECONDS` | `10` | Frecuencia de lecturas |
| `BASE_TEMPERATURE_CELSIUS` | `19.5` | Temperatura inicial |

El simulador crea la boya automáticamente si todavía no existe.
