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

El chart incluye una integración opcional con Secrets Store CSI Driver. Para
usarla, instala previamente el driver y habilita el bloque con los valores de
Key Vault:

```bash
helm upgrade --install tidewatch ./helm/tidewatch \
  --set workloadIdentity.enabled=true \
  --set workloadIdentity.clientId=<USER_ASSIGNED_IDENTITY_CLIENT_ID> \
  --set keyVault.enabled=true \
  --set keyVault.name=<KEY_VAULT_NAME> \
  --set keyVault.tenantId=<TENANT_ID> \
  --set keyVault.databaseSecretName=database-url
```

La opción sincroniza el secreto `DATABASE_URL` con el Secret Kubernetes que
consume la API; cuando está activa, la API lee el fichero montado para evitar
depender de que el Secret exista antes del primer arranque. Permanece
desactivada por defecto y requiere validar el acceso en un AKS real antes de
usarla en producción.
Al activar Key Vault, el chart asocia automáticamente la ServiceAccount de
Workload Identity al pod de la API.

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

La estimación experimental de oleaje usa `api.waveImuHeightFactor` para
convertir la variabilidad vertical de la IMU. Su valor por defecto es `0.1`;
ajústalo solo con datos de calibración de la boya y mantén documentado el
valor usado en cada entorno.
