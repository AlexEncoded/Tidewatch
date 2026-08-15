# Load tests

Las pruebas de carga validarán la ingesta y las lecturas de la API antes de
desplegar un entorno Azure. Se usará k6 para mantener el escenario ligero y
reproducible.

## Ejecutar

Con la API local levantada:

```bash
k6 run -e BASE_URL=http://localhost:8000 load-tests/telemetry.js
```

El escenario empieza con lecturas de salud y de flota, y después consulta
incidencias de mantenimiento. No crea datos ni debe ejecutarse contra
producción sin una ventana aprobada.
