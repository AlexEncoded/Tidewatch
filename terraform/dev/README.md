# Development environment

Entorno Azure de desarrollo. Usará nombres y recursos separados de staging y
producción. La configuración sensible se inyectará desde el entorno de ejecución.

## Recursos iniciales

- Resource Group `rg-tidewatch-dev`.
- Azure Container Registry para las imágenes de API y worker.
- Log Analytics Workspace para la futura observabilidad de AKS.
- PostgreSQL Flexible Server privado con Private DNS y backup.

## Uso

```bash
az login
az account set --subscription <SUBSCRIPTION_ID>
copy terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
terraform plan -out dev.tfplan
```

El `apply` se hará después de revisar nombres, región y presupuesto. El ACR
está configurado sin usuario administrador; el acceso futuro se realizará con
Managed Identity. PostgreSQL requiere una contraseña sensible y puede generar
costes, por lo que no debe desplegarse hasta confirmar el presupuesto.
