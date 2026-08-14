# Tidewatch Helm chart

Chart para desplegar la API y el simulador de boyas en AKS.

## Requisito

Debe existir un Secret con la URL de PostgreSQL:

```bash
kubectl create secret generic tidewatch-database \
  --from-literal=DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/tidewatch'
```

En producción, este Secret será sustituido por Azure Key Vault y Workload
Identity. No se deben guardar credenciales en `values.yaml`.

## Instalar

```bash
helm upgrade --install tidewatch ./helm/tidewatch \
  --namespace tidewatch \
  --create-namespace
```

Para usar imágenes de ACR:

```bash
helm upgrade --install tidewatch ./helm/tidewatch \
  --set api.image.repository=<ACR_NAME>.azurecr.io/tidewatch-api \
  --set api.image.tag=<IMAGE_TAG> \
  --set worker.image.repository=<ACR_NAME>.azurecr.io/tidewatch-worker \
  --set worker.image.tag=<IMAGE_TAG>
```
