# Disaster recovery

Procedimientos públicos de backup, restauración y recuperación ante fallos.

## Objetivo

La pérdida de una instancia de API no debe implicar pérdida de telemetría: los
datos deben recuperarse desde PostgreSQL y las aplicaciones deben reconstruirse
desde imágenes versionadas en ACR y manifiestos Git.

## Estado actual

La estrategia está documentada como objetivo y todavía no se ha probado en un
entorno Azure desplegado. El volumen PostgreSQL de Docker Compose es solo para
desarrollo local y no constituye un backup.

## Procedimiento previsto

1. Confirmar el incidente y congelar cambios de despliegue.
2. Recuperar PostgreSQL Flexible Server desde un backup o punto de restauración.
3. Verificar la cadena de migraciones Alembic antes de levantar la API.
4. Restaurar secretos mediante Key Vault y Workload Identity.
5. Reconciliar AKS con Argo CD y comprobar health checks.
6. Validar `/health`, `/metrics`, ingesta y consultas recientes.
7. Registrar tiempos, pérdida de datos y acciones en un postmortem.

## Prueba local controlada

Con PostgreSQL local y `DATABASE_URL` apuntando a una base de pruebas, generar
un backup con:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://tidewatch:tidewatch@localhost:5432/tidewatch"
./scripts/postgres-backup.ps1 -OutputFile ./.tmp/tidewatch-backup.dump
```

Restaurarlo requiere una confirmación explícita porque `pg_restore --clean`
elimina objetos existentes en la base destino:

```powershell
./scripts/postgres-restore.ps1 -BackupFile ./.tmp/tidewatch-backup.dump -ConfirmRestore
cd apps/api
alembic upgrade head
```

Después de restaurar, ejecutar los smoke checks de `/health`, `/metrics`, una
ingesta y una consulta. Los helpers no se ejecutan automáticamente ni apuntan
a Azure por defecto.

## Pruebas pendientes

- Restauración real de PostgreSQL Flexible Server.
- Recuperación de AKS desde Terraform y Argo CD.
- Medición de RPO/RTO.
- Simulación de pérdida de una zona Azure.
