# Tidewatch frontend

Dashboard operativo inicial para consultar la flota de boyas, su temperatura,
estado y última comunicación.

## Ejecutar con Docker Compose

```bash
docker compose up --build
```

Abrir <http://localhost:8080>.

Nginx hace proxy de `/api/` hacia el servicio interno de la API. El dashboard
se actualiza automáticamente cada 15 segundos.

Cada tarjeta muestra también el resumen acumulado de calidad de datos de la
boya: lecturas `good`, `suspect` e `invalid`. Las lecturas inválidas siguen
siendo visibles en el histórico, pero no participan en los análisis. También
muestra la velocidad media y distancia recorrida cuando existen posiciones
suficientes para calcular el movimiento. El mapa dibuja además la trayectoria
reciente de cada boya a partir de su histórico de posiciones.
