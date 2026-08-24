# Chaos experiments

Los experimentos de chaos se ejecutarán únicamente en entornos controlados y
con una ventana de recuperación aprobada. Ningún experimento debe apuntar a
producción por defecto.

## Experimentos iniciales

| Experimento | Objetivo | Señal de éxito |
|---|---|---|
| Parar el simulador | Validar detección de boya silenciosa | `TidewatchBuoySilent` aparece dentro del umbral |
| Bloquear temporalmente la API | Validar health checks y recuperación | Kubernetes reinicia o recupera el servicio |
| Eliminar un pod worker | Validar reconciliación GitOps | Argo CD/Deployment recupera la réplica |
| Inyectar discrepancia A/B | Validar salud de sensores | Aparece `TidewatchSensorDegraded` |

El experimento reproducible `inject_ab_discrepancy.py` crea una boya efímera,
envía dos temperaturas A/B divergentes y verifica que la API marque el sensor
como `degraded`:

```bash
python chaos/inject_ab_discrepancy.py --api-url http://localhost:8000
```

Solo debe ejecutarse contra un entorno local o efímero. La boya creada debe
eliminarse según el procedimiento de limpieza del entorno tras la prueba.

## Reglas

- Documentar hipótesis, duración, entorno y rollback antes de empezar.
- Observar `/health`, `/metrics`, logs y cola de mantenimiento.
- Detener el experimento si afecta a datos persistidos.
- Registrar resultados en `postmortems/` cuando se descubra una debilidad.
