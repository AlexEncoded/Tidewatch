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

## Reglas

- Documentar hipótesis, duración, entorno y rollback antes de empezar.
- Observar `/health`, `/metrics`, logs y cola de mantenimiento.
- Detener el experimento si afecta a datos persistidos.
- Registrar resultados en `postmortems/` cuando se descubra una debilidad.
