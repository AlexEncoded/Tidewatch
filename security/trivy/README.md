# Trivy

Trivy se ejecuta en GitHub Actions para analizar:

- Dependencias y archivos del repositorio.
- Configuración Terraform y Kubernetes.
- Secretos detectables.
- Imágenes Docker de API y worker.

El pipeline falla ante vulnerabilidades `HIGH` o `CRITICAL` no corregidas. Las
excepciones deberán documentarse y limitarse con un archivo `.trivyignore` solo
cuando exista una justificación técnica.
