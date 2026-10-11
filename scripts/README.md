# Azure scripts

Scripts auxiliares para autenticación, bootstrap, validación y operaciones.

Los scripts deben ser idempotentes y comprobar siempre la suscripción y el
entorno antes de modificar recursos.

Ejemplo de contexto esperado:

```bash
az account show
az aks get-credentials --resource-group <RESOURCE_GROUP> --name <AKS_NAME>
```

## Simulador de telemetría

Con la API local levantada, el simulador crea una boya de prueba y envía cada
10 segundos lecturas A/B de temperatura, presión, salinidad y batería:

```bash
python scripts/telemetry_simulator.py
```

Para enviar un único lote o reutilizar una boya existente:

```bash
python scripts/telemetry_simulator.py --once
python scripts/telemetry_simulator.py --buoy-id TW-XXXXXXXX --interval 5
```

## Evaluación experimental del oleaje

Para comparar el estimador GNSS/IMU con alturas de ola de referencia medidas
independientemente, usa el evaluador offline. Requiere ventanas separadas de
calibración y validación; no modifica la configuración de la API:

```bash
python scripts/evaluate-wave-calibration.py data/labeled-waves.csv
```

El formato CSV y las precauciones para interpretar los resultados están en
[`docs/wave-calibration.md`](../docs/wave-calibration.md).
