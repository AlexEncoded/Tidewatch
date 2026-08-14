# Azure Infrastructure

Infraestructura de Azure gestionada con Terraform.

## Recursos previstos

| Área | Servicio Azure |
|---|---|
| Red | Virtual Network, subnets, NSG y Private DNS |
| Contenedores | AKS y Azure Container Registry |
| Datos | PostgreSQL Flexible Server |
| Secretos | Azure Key Vault |
| Observabilidad | Log Analytics, Azure Monitor y Managed Prometheus |
| Identidad | Microsoft Entra ID y Managed Identity |

## Convenciones

- Cada entorno vive en su propia carpeta (`dev`, `staging`, `production`).
- Los secretos se obtienen desde Key Vault o desde el pipeline; nunca se guardan
  en `.tfvars` versionados.
- El estado remoto se almacenará en Azure Storage con bloqueo mediante Blob Lease.
- Los nombres y tags deben incluir entorno, aplicación y propietario.

## Requisitos locales

```bash
az login
az account set --subscription <SUBSCRIPTION_ID>
terraform init
terraform validate
terraform plan
```

Antes de ejecutar `apply` hay que crear el Storage Account del estado remoto y
configurar el backend según el entorno.
