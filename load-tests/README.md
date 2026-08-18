# Load tests

Las pruebas de carga validarán la ingesta y las lecturas de la API antes de
desplegar un entorno Azure. Se usará k6 para mantener el escenario ligero y
reproducible.

## Ejecutar

Con la API local levantada:

```bash
k6 run -e BASE_URL=http://localhost:8000 load-tests/telemetry.js
```

El escenario crea una boya efímera al comenzar y envía siete lecturas por
iteración mediante el endpoint batch: dos canales por sensor ambiental y una
lectura de batería. Después consulta salud, flota e incidencias de
mantenimiento. Genera datos de prueba y no debe ejecutarse contra producción
sin una ventana aprobada. También persiste una evaluación de salud A/B y
consulta su histórico en cada iteración para medir el coste operativo de las
decisiones de fallback.
