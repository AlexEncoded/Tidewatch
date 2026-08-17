# Tidewatch Helm chart

Chart para desplegar el frontend, la API y el simulador de boyas en AKS.

## Requisito

Debe existir un Secret con la URL de PostgreSQL:

```bash
kubectl create secret generic tidewatch-database \
  --from-literal=DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/tidewatch'
```

En producción, este Secret será sustituido por Azure Key Vault y Workload
Identity. No se deben guardar credenciales en `values.yaml`.

Para activar Workload Identity en el API, usa el `client_id` de la salida
`tidewatch_api_workload_identity_client_id` de Terraform:

```bash
helm upgrade --install tidewatch ./helm/tidewatch \
  --set workloadIdentity.enabled=true \
  --set workloadIdentity.clientId=<USER_ASSIGNED_IDENTITY_CLIENT_ID>
```

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

El Ingress está desactivado por defecto. Para activarlo cuando exista un
controller compatible:

```bash
helm upgrade --install tidewatch ./helm/tidewatch \
  --set ingress.enabled=true \
  --set ingress.className=nginx \
  --set ingress.host=tidewatch.example.com
```
