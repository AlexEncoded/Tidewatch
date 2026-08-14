# Tidewatch

> Plataforma cloud-native para supervisar redes de boyas oceánicas autónomas,
> procesar telemetría y detectar anomalías marítimas en tiempo casi real.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](#integración-y-entrega)
[![Cloud](https://img.shields.io/badge/Cloud-Microsoft%20Azure-0078D4?logo=microsoftazure&logoColor=white)](#arquitectura)
[![Runtime](https://img.shields.io/badge/Runtime-AKS-326CE5?logo=kubernetes&logoColor=white)](#arquitectura)
[![IaC](https://img.shields.io/badge/IaC-Terraform-844FBA?logo=terraform&logoColor=white)](#infraestructura)

## Resumen

Tidewatch centraliza la información de una flota de boyas instrumentadas que
recogen oleaje, temperatura, salinidad, presión y posición. La plataforma
recibe telemetría, la valida, identifica lecturas anómalas y presenta el estado
operativo de la red a los equipos de oceanografía y mantenimiento.

El producto de negocio es deliberadamente acotado. El foco del repositorio está
en construir una plataforma reproducible, segura y observable capaz de llevar
una señal desde el dispositivo hasta una operación en producción.

## Capacidades previstas

- Vista operativa de la flota y estado de cada boya.
- Ingesta de telemetría y procesamiento asíncrono.
- Detección de anomalías y generación de incidencias.
- Historial de mediciones y trazabilidad de eventos.
- Simulación de dispositivos para desarrollo y pruebas de carga.
- Despliegues progresivos con rollback.
- Métricas de producto y métricas DORA.

## Arquitectura

```text
Simuladores / Boyas
        │
        ▼
      API ───────────────► PostgreSQL Flexible Server
        │
        ▼
     Worker ─────────────► Alertas y anomalías
        │
        ▼
   Frontend operativo

GitHub Actions → Azure Container Registry → Argo CD → Azure Kubernetes Service
                                                        │
                         Azure Monitor · Log Analytics · Managed Grafana
```

### Servicios principales

| Área | Servicio o tecnología |
|---|---|
| Aplicación | Frontend, API y worker en contenedores |
| Cloud | Microsoft Azure |
| Compute | Azure Kubernetes Service (AKS) |
| Imágenes | Azure Container Registry (ACR) |
| Datos | Azure Database for PostgreSQL - Flexible Server |
| Secretos | Azure Key Vault y Workload Identity |
| Infraestructura | Terraform y Azure Resource Manager |
| Entrega | GitHub Actions, Helm y Argo CD |
| Observabilidad | Azure Monitor, Log Analytics, Prometheus y Grafana |
| Seguridad | Microsoft Entra ID, Trivy, Kyverno y Defender for Cloud |

## Estructura del repositorio

```text
apps/             Aplicaciones de Tidewatch
terraform/        Infraestructura de Azure por entorno
kubernetes/       Manifiestos base y overlays de AKS
helm/             Charts de despliegue
argocd/            Configuración GitOps
observability/    Métricas, logs, dashboards y alertas
security/         Políticas y análisis de seguridad
load-tests/       Pruebas de carga de la ingesta
chaos/            Experimentos de resiliencia
scripts/          Automatización operativa
runbooks/         Procedimientos de operación
postmortems/      Análisis de incidentes
docs/             Documentación pública
PLANNING/         Diario privado de aprendizaje y decisiones
```

## Integración y entrega

Cada cambio deberá atravesar, como mínimo:

1. Linting, tests y validación de contratos.
2. Análisis estático y detección de secretos.
3. Construcción y escaneo de imágenes.
4. Despliegue en desarrollo y smoke tests.
5. Promoción controlada a staging y producción.

La infraestructura se tratará como código y los despliegues de Kubernetes se
gestionarán mediante GitOps.

## Continuous integration

GitHub Actions valida automáticamente la API, ejecuta los tests, compila el
código Python, construye las imágenes Docker y valida la configuración de
Terraform para `dev`.

## Puesta en marcha local

Requisitos iniciales:

- Docker
- Azure CLI
- Terraform
- kubectl
- Helm

```bash
az login
az account set --subscription <SUBSCRIPTION_ID>
docker compose up --build
```

La configuración específica de cada entorno y las credenciales deben inyectarse
desde el entorno de ejecución. No se almacenan secretos en el repositorio.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Infraestructura Azure](terraform/README.md)
- [Seguridad](docs/security.md)
- [Disaster recovery](docs/disaster-recovery.md)
- [Runbooks](runbooks/)
- [Postmortems](postmortems/)

## Estado del proyecto

En fase de definición de plataforma y arquitectura base.

## Licencia

Pendiente de definir.
