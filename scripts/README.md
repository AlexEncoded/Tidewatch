# Azure scripts

Scripts auxiliares para autenticación, bootstrap, validación y operaciones.

Los scripts deben ser idempotentes y comprobar siempre la suscripción y el
entorno antes de modificar recursos.

Ejemplo de contexto esperado:

```bash
az account show
az aks get-credentials --resource-group <RESOURCE_GROUP> --name <AKS_NAME>
```
