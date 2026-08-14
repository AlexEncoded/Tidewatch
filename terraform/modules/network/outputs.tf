output "virtual_network_id" {
  value       = azurerm_virtual_network.main.id
  description = "Virtual Network resource ID."
}

output "aks_subnet_id" {
  value       = azurerm_subnet.aks.id
  description = "AKS subnet resource ID."
}

output "postgres_subnet_id" {
  value       = azurerm_subnet.postgres.id
  description = "PostgreSQL subnet resource ID."
}
