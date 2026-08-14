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
