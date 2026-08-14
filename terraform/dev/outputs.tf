output "resource_group_name" {
  description = "Development resource group name."
  value       = azurerm_resource_group.main.name
}

output "container_registry_login_server" {
  description = "ACR login server for image tags."
  value       = azurerm_container_registry.main.login_server
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace resource ID."
  value       = azurerm_log_analytics_workspace.main.id
}

output "aks_subnet_id" {
  description = "Subnet reserved for AKS."
  value       = module.network.aks_subnet_id
}

output "postgres_subnet_id" {
  description = "Subnet reserved for PostgreSQL Flexible Server."
  value       = module.network.postgres_subnet_id
}

output "postgres_server_fqdn" {
  description = "Private PostgreSQL server hostname."
  value       = module.postgres.fully_qualified_domain_name
}

output "aks_cluster_name" {
  description = "AKS cluster name."
  value       = module.aks.cluster_name
}

output "aks_oidc_issuer_url" {
  description = "AKS OIDC issuer URL for Workload Identity."
  value       = module.aks.oidc_issuer_url
}
