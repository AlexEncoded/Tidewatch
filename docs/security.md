# Security

Modelo de seguridad, controles, amenazas y prácticas DevSecOps del proyecto.

La identidad principal será Microsoft Entra ID. Se priorizarán Managed
Identities y AKS Workload Identity frente a secretos estáticos.

## Controles actuales

- GitHub Actions ejecuta tests, compilación de contenedores, Terraform,
  Gitleaks y Trivy.
- Las imágenes API y worker ejecutan como usuarios no root.
- Los deployments Helm usan `runAsNonRoot`, capacidades Linux vacías,
  `allowPrivilegeEscalation: false` y filesystem de solo lectura.
- Kyverno y las etiquetas Pod Security protegen los namespaces de Kubernetes.
- AKS tiene RBAC y rangos autorizados para el API server definidos en Terraform.
- Key Vault usa RBAC y ACL de red con acción por defecto `Deny`.

## Pendiente

- Completar Workload Identity y retirar secretos de configuración local.
- Añadir notificaciones externas sin exponer datos de telemetría.
- Incorporar escaneo y políticas de calidad de datos.
- Revisar dependencias y versiones de acciones periódicamente.
