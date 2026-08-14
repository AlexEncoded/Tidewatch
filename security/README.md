# Azure security

- Microsoft Entra ID para identidad y acceso.
- Managed Identity y AKS Workload Identity para evitar credenciales estáticas.
- Azure Key Vault para secretos y certificados.
- Microsoft Defender for Cloud para postura y recomendaciones.
- Trivy para imágenes y dependencias.
- Kyverno para políticas de admisión en Kubernetes.
- Private Endpoints y Azure Policy cuando el entorno lo requiera.

El workflow `security.yml` ejecuta Gitleaks y Trivy sobre el repositorio y las
imágenes Docker antes de que puedan publicarse en ACR.
