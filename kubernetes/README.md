# Kubernetes on AKS

Los manifiestos están destinados a Azure Kubernetes Service.

- `base/` contiene recursos comunes.
- `overlays/` contiene diferencias por entorno.
- Las imágenes se publican en Azure Container Registry.
- Los secretos de aplicación deberán integrarse con Azure Key Vault mediante
  Workload Identity y Secrets Store CSI Driver.
- El acceso externo se resolverá con Azure Application Gateway for Containers o
  un ingress controller compatible con AKS.

La base de Kustomize aplica límites de recursos y una cuota por namespace. El
overlay `overlays/dev` crea el namespace de desarrollo con etiquetas de Pod
Security. Los Deployments de API y worker los gestiona Helm.
