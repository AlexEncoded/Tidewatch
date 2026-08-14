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
