# ADR-0001: Azure como plataforma y GitOps para despliegues

- Estado: aceptada
- Fecha: 2026-08-15

## Contexto

Tidewatch necesita demostrar una plataforma cloud-native completa sin
desplegar recursos con coste de forma accidental. El proyecto debe mantener
infraestructura, seguridad y despliegues reproducibles.

## Decisión

- Azure será el proveedor cloud de referencia.
- Terraform definirá red, AKS, ACR, PostgreSQL Flexible Server y Key Vault.
- GitHub Actions validará código, infraestructura, imágenes y seguridad.
- Helm empaquetará la aplicación y Argo CD reconciliará los despliegues en AKS.
- Los entornos con coste requerirán aprobación explícita.

## Consecuencias

Esta decisión permite practicar IaC, CI/CD, GitOps, observabilidad y seguridad
con una ruta clara hacia GPU y procesamiento distribuido en Azure. También
obliga a controlar cuidadosamente permisos, secretos y costes antes de aplicar
Terraform.

## Alternativas descartadas por ahora

- Kubernetes local como plataforma principal: útil para pruebas, pero no cubre
  el objetivo Azure del proyecto.
- Despliegues manuales desde la máquina del desarrollador: no son auditables ni
  reproducibles.
