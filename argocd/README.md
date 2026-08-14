# Argo CD on AKS

Configuración GitOps para sincronizar los overlays de Kubernetes en AKS.

Argo CD se autenticará usando Microsoft Entra ID y las aplicaciones utilizarán
identidades administradas cuando necesiten acceder a servicios de Azure.

La primera aplicación está en `applications/tidewatch-dev.yaml`. Apunta al
chart de `helm/tidewatch` y utiliza `values-dev.yaml` para el entorno de
desarrollo.

Antes de sincronizarla en AKS hay que crear el Secret `tidewatch-database` en el
namespace de destino. Más adelante lo sustituiremos por Azure Key Vault y
Workload Identity.
