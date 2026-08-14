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

## Capacidades actuales

- API para registrar boyas y lecturas de temperatura, presión y salinidad.
- Persistencia PostgreSQL con migraciones Alembic.
- Simulador de telemetría de boyas.
- Análisis de media, rango, tendencia y anomalías.
- Alertas derivadas y alertas persistidas con resolución.
- Ubicación, estado operativo y última comunicación de cada boya.
- Presión en kPa como base para el futuro cálculo de altura de ola.
- Estimación experimental de altura de ola a partir de variación de presión.
- Clasificación operativa inicial del estado del mar.
- Salinidad en PSU para enriquecer la telemetría oceanográfica.
- Canales redundantes A/B y endpoint de comparación de salud de sensores.
- Telemetría de batería y avisos de carga baja para mantenimiento.
- Métricas Prometheus y dashboard Grafana.
- Chart Helm, aplicación Argo CD y políticas base de Kubernetes.
- Infraestructura Azure preparada con Terraform.

## Dirección del proyecto

Tidewatch crecerá por iteraciones pequeñas. Cada nueva capacidad deberá aportar
valor a la operación de las boyas y, al mismo tiempo, mejorar la plataforma:
reproducibilidad, seguridad, observabilidad, resiliencia o automatización.

La infraestructura Azure está definida como código, pero los recursos con coste
(PostgreSQL Flexible Server y AKS) no se despliegan automáticamente durante
esta fase de aprendizaje.

## Roadmap y TODO

### Próximos pasos

- [ ] Validar el chart Helm con `helm lint` y desplegarlo en un clúster local.
- [ ] Completar el flujo Azure Key Vault + Workload Identity.
- [ ] Publicar API y worker en ACR desde GitHub Actions.
- [ ] Desplegar AKS `dev` con aprobación explícita.
- [x] Añadir mapa operativo de boyas al frontend.
- [ ] Crear tests de carga para la ingesta.

### Evolución de la plataforma

- [x] Añadir soporte inicial para sensores duplicados A/B.
- [ ] Modelar calidad y procedencia de cada lectura.
- [x] Añadir salinidad y primera estimación experimental de oleaje derivada de presión.
- [x] Mostrar condiciones oceánicas y estado del mar en el frontend.
- [ ] Calibrar el oleaje con datos reales y añadir posición dinámica.
- [ ] Crear procesamiento asíncrono real para telemetría.
- [ ] Incorporar notificaciones de mantenimiento.
- [ ] Añadir entornos `staging` y `production`.
- [ ] Implementar blue/green o canary deployments.
- [ ] Añadir backups, restauración y disaster recovery probado.
- [ ] Introducir load tests y chaos engineering.
- [ ] Medir métricas DORA y coste por entorno.

### Futuro experimental: datos y ML

- [ ] Acumular histórico suficiente de las boyas.
- [ ] Procesar ventanas recientes mediante un flujo continuo.
- [ ] Distribuir trabajos entre workers.
- [ ] Probar un modelo simulado en CPU.
- [ ] Levantar GPUs en Azure solo cuando el experimento lo justifique.
- [ ] Versionar datasets, modelos y predicciones.

El detalle de estas ideas, decisiones y aprendizajes se mantiene en `PLANNING/`.

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

También se ejecutan análisis de secretos, configuración y vulnerabilidades con
Gitleaks y Trivy.

La configuración de Helm y Kustomize también se renderiza automáticamente en
CI para detectar errores de despliegue antes de llegar a AKS.

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

Fase actual: **fundación de plataforma**. La API de temperatura, presión y
salinidad funciona en local, la persistencia y el pipeline de CI están
preparados, y la infraestructura Azure está definida como código pendiente de
despliegue controlado.

## Licencia

Pendiente de definir.
