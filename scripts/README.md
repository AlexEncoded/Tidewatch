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
